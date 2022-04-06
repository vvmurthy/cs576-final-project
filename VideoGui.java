import java.awt.*;
import java.awt.event.*;
import java.awt.image.*;
import java.io.*;
import javax.swing.*;
import java.io.BufferedInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.util.Queue;
import java.util.concurrent.ConcurrentLinkedQueue;

import javax.sound.sampled.AudioFormat;
import javax.sound.sampled.AudioInputStream;
import java.util.concurrent.atomic.AtomicReference;
import javax.sound.sampled.AudioSystem;
import javax.sound.sampled.LineUnavailableException;
import javax.sound.sampled.SourceDataLine;
import javax.sound.sampled.UnsupportedAudioFileException;
import javax.sound.sampled.DataLine.Info;

public class VideoGui {
    public class PlaySound {
        private InputStream waveStream;
        
        private final int EXTERNAL_BUFFER_SIZE = 128000; // 128kb

        private SourceDataLine dataLine = null; 
        AudioInputStream audioInputStream = null;

        /**
        * CONSTRUCTOR
        */
        public PlaySound(InputStream waveStream) {
            this.waveStream = waveStream;
        }

        public void load() throws UnsupportedAudioFileException,
        LineUnavailableException, IOException{
            InputStream bufferedIn = new BufferedInputStream(this.waveStream);
            audioInputStream = AudioSystem.getAudioInputStream(bufferedIn);
            
            // Obtain the information about the AudioInputStream
            AudioFormat audioFormat = audioInputStream.getFormat();
            Info info = new Info(SourceDataLine.class, audioFormat);

            // opens the audio channel
            dataLine = (SourceDataLine) AudioSystem.getLine(info);
            dataLine.open(audioFormat, this.EXTERNAL_BUFFER_SIZE);

            // skips bits

            int init = (int)framesToBytes();
            if(init > 0) {
                byte[] initBuffer = new byte[init];
            audioInputStream.read(initBuffer, 0,
                    initBuffer.length);
            }
            
            
        }

        public void pause(){
            dataLine.stop();
        }

        public void play() throws UnsupportedAudioFileException,
        LineUnavailableException, IOException  {

            // Starts the music :P
            dataLine.start();

            int readBytes = 0;
            byte[] audioBuffer = new byte[this.EXTERNAL_BUFFER_SIZE];

            try {
                
                while (readBytes != -1) {
                    readBytes = audioInputStream.read(audioBuffer, 0,
                        audioBuffer.length);
                    if (readBytes >= 0){
                        dataLine.write(audioBuffer, 0, readBytes);
                    }
                }
            } finally {
                // plays what's left and and closes the audioChannel
                dataLine.drain();
                dataLine.close();
            }

        }
    }

    private JButton play;
    private final long latency = 33; // ms
    private ImageIcon icon;
    private boolean isPlaying = false;
    private final Queue<BufferedImage> myQ = new ConcurrentLinkedQueue<BufferedImage>();
    JFrame frame;
    JLabel lbIm1;
    BufferedImage imgOne;
    
    final int BUFFER_SIZE = 30 * 60 * 5;
    final int WIDTH = 480; // default image width and height
    final int HEIGHT = 270;

    private int framesRead = 0;

    private final BufferedImage newImg = new BufferedImage(WIDTH, HEIGHT, BufferedImage.TYPE_INT_RGB);

    
    /**
     * Read Image RGB
     * Reads the image of given width and height at the given imgPath into the
     * provided BufferedImage.
     */
    private void readFrameRgb(int width, int height, RandomAccessFile raf, BufferedImage img) throws EOFException, IOException  {
        int frameLength = width * height * 3;
        long len = frameLength;
        byte[] bytes = new byte[(int) len];

        raf.read(bytes);

        int ind = 0;
        for (int y = 0; y < height; y++) {
            for (int x = 0; x < width; x++) {
                byte r = bytes[ind];
                byte g = bytes[ind + height * width];
                byte b = bytes[ind + height * width * 2];

                int pix = 0xff000000 | ((r & 0xff) << 16) | ((g & 0xff) << 8) | (b & 0xff);
                img.setRGB(x, y, pix);
                ind++;
            }
        }
       
    }

    public void readSingleImage(RandomAccessFile raf) throws Exception{
        if(myQ.size() < BUFFER_SIZE) {
            BufferedImage img = new BufferedImage(WIDTH, HEIGHT, BufferedImage.TYPE_INT_RGB);
            readFrameRgb(WIDTH, HEIGHT, raf, img);
            myQ.add(img);
            
        } 
    }

    public void fillQueue(RandomAccessFile raf, boolean breakWhenDone) {
        
        try{
            while(true) {
                if(myQ.size() < BUFFER_SIZE) {
                    readSingleImage(raf);
                    
                } else if(breakWhenDone) {
                    break;
                }
            }
            
        }catch(Exception ee) {
            ee.printStackTrace();
        }
    }
    public void playVideo(){
        long decodeTime = 0;
        long prevStart = 0;
        long sleepTime = 0;
        isPlaying = true;
        int i = 0;
        long nextIterLatency = 0;
        long start = System.currentTimeMillis();
        while(true){
            prevStart = start;
            System.out.println(myQ.size());
            start = System.currentTimeMillis();
            if(!isPlaying) {
                continue;
            }
            long decodeIterTime = (start - prevStart - sleepTime);
             
            imgOne = myQ.poll();
            framesRead++;
            if(imgOne == null || myQ.size() == 0){
                System.out.println("Invalid image " + myQ.size());
                break;
            } 
            icon.setImage(imgOne);
            
            i++;
            if(i % 3 == 0) {
                sleepTime = latency - decodeIterTime + 1;
            } else {
                sleepTime = latency - decodeIterTime;
            }
            
            frame.repaint();
            frame.invalidate();

            // correct so the latency takes into account the processing
            // time of the decoding
            if(decodeIterTime < latency) {
                try {
                    Thread.sleep(sleepTime);
                } catch (InterruptedException er) {
                    // dont really care
                }
            } else {
                long framesToToss = (sleepTime * -1) / latency;
                while(framesToToss > 0) {
                    myQ.poll();
                    framesRead++;
                    framesToToss--;
                }
                sleepTime = -1 *( (sleepTime * -1) % latency);
            }
        }
    }

    public long framesToBytes() {
        double secondsPassed = framesRead / 30.0;
        double bytes = 48000 * secondsPassed * 16 / 8;

        return Math.round(bytes);
    }

    public void showIms(String[] args) throws Exception {

        // Read a parameter from command line
        if (args.length < 2) {
            System.out.println("Need 2 args: inputVideo inputAudio");
            return;
        }

        if(! new File(args[0]).exists()) {
            System.out.println("image file does not exist");
            return;
        }
        if(! new File(args[1]).exists()) {
            System.out.println("audio file does not exist");
            return;
        }
        final File file = new File(args[0]);
        RandomAccessFile raf = new RandomAccessFile(file, "r");
        raf.seek(0);

        
        fillQueue(raf, true);

        imgOne = new BufferedImage(WIDTH, HEIGHT, BufferedImage.TYPE_INT_RGB);
        

        // Use label to display the image
        frame = new JFrame();
        GridBagLayout gLayout = new GridBagLayout();
        frame.getContentPane().setLayout(gLayout);

        GridBagConstraints a = new GridBagConstraints();
        a.fill = GridBagConstraints.HORIZONTAL;
        a.anchor = GridBagConstraints.CENTER;
        a.weightx = 0.5;
        a.gridx = 0;
        a.gridy = 0;

        GridBagConstraints b = new GridBagConstraints();
        b.fill = GridBagConstraints.HORIZONTAL;
        b.anchor = GridBagConstraints.CENTER;
        b.weightx = 0.5;
        b.gridx = 0;
        b.gridy = 1;

        GridBagConstraints c = new GridBagConstraints();
        c.fill = GridBagConstraints.HORIZONTAL;
        c.anchor = GridBagConstraints.CENTER;
        c.weightx = 0.5;
        c.gridx = 0;
        c.gridy = 2;

        play = new JButton("Pause");
        
        icon = new ImageIcon(imgOne);
        JLabel orig = new JLabel(icon);
        lbIm1 = new JLabel(new ImageIcon(newImg));
        JLabel original = new JLabel("Original");

        frame.getContentPane().removeAll();
        frame.getContentPane().add(original, a);
        frame.getContentPane().add(orig, b);
        frame.getContentPane().add(play, c);

        frame.pack();
        frame.setVisible(true);

        // opens the inputStream
        FileInputStream inputStream;
        try {
            inputStream = new FileInputStream(args[1]);
        } catch (FileNotFoundException fe) {
            fe.printStackTrace();
            return;
        }


        // initializes the playSound Object
        final AtomicReference<PlaySound> playSound = new AtomicReference<>();
        playSound.set(new PlaySound(inputStream));
        
        Thread thread = new Thread(){
            public void run(){
                try{
                playSound.get().play();
                }catch(Exception ee) {
                    ee.printStackTrace();
                }
            }
        };
        playSound.get().load();
        thread.start();
        Thread.sleep(500);
                
        play.addActionListener(new ActionListener() {

            @Override
            public void actionPerformed(ActionEvent e) {
                if(isPlaying) {
                    isPlaying = false;
                    play.setText("Play");
                    playSound.get().pause();
                    thread.stop();
                } else {
                    isPlaying = true;
                    play.setText("Pause");
                    try {
                        FileInputStream inputStream = new FileInputStream(args[1]);
                        
                        playSound.set(new PlaySound(inputStream));
        
                        Thread t = new Thread(){
                            public void run(){
                                try{
                                    playSound.get().play();
                                }catch(Exception ee) {
                                    ee.printStackTrace();
                                }
                            }
                        };
                        playSound.get().load();

                        t.start();
                    }catch(Exception wee) {

                    }
                    
                    
                }
            }
        });
        

        playVideo();
        System.out.println("Done.");
    }

    public static void main(String[] args) throws Exception {
    
        VideoGui ren = new VideoGui();
        ren.showIms(args);
    }

}