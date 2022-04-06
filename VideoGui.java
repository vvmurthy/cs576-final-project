import java.awt.*;
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
import javax.sound.sampled.AudioSystem;
import javax.sound.sampled.LineUnavailableException;
import javax.sound.sampled.SourceDataLine;
import javax.sound.sampled.UnsupportedAudioFileException;
import javax.sound.sampled.DataLine.Info;

public class VideoGui {
    public class PlaySound {
        private InputStream waveStream;
        
        private final int EXTERNAL_BUFFER_SIZE = 10000000; // 3mb

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
    private final Queue<BufferedImage> myQ = new ConcurrentLinkedQueue<BufferedImage>();
    JFrame frame;
    JLabel lbIm1;
    BufferedImage imgOne;
    
    final int BUFFER_SIZE = 30 * 60 * 5;
    final int WIDTH = 480; // default image width and height
    final int HEIGHT = 270;

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

        long latency = 33; // ms
        fillQueue(raf, true);

        imgOne = new BufferedImage(WIDTH, HEIGHT, BufferedImage.TYPE_INT_RGB);
        Thread tt = new Thread(){
            public void run(){
                fillQueue(raf, false);
            }
        };
        tt.setPriority(Thread.MAX_PRIORITY);
        //tt.start();

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
        c.gridx = 1;
        c.gridy = 0;

        GridBagConstraints d = new GridBagConstraints();
        d.fill = GridBagConstraints.HORIZONTAL;
        d.anchor = GridBagConstraints.CENTER;
        d.weightx = 0.5;
        d.gridx = 1;
        d.gridy = 1;

        GridBagConstraints e = new GridBagConstraints();
        e.fill = GridBagConstraints.HORIZONTAL;
        e.anchor = GridBagConstraints.CENTER;
        e.weightx = 0.5;
        e.gridx = 2;
        e.gridy = 0;

        play = new JButton("Play");
        ImageIcon icon = new ImageIcon(imgOne);
        JLabel orig = new JLabel(icon);
        lbIm1 = new JLabel(new ImageIcon(newImg));
        JLabel decoded = new JLabel("Decoded");
        JLabel original = new JLabel("Original");

        frame.getContentPane().removeAll();
        frame.getContentPane().add(original, a);
        frame.getContentPane().add(orig, b);
        frame.getContentPane().add(decoded, c);
        frame.getContentPane().add(lbIm1, d);
        frame.getContentPane().add(play, e);

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
        final PlaySound playSound = new PlaySound(inputStream);
        long decodeTime = 0;
        long prevStart = 0;
        long sleepTime = 0;
        
        int i = 0;
        long nextIterLatency = 0;
        playSound.load();

        try{
                
                    Thread thread = new Thread(){
                        public void run(){
                            try{
                            playSound.play();
                            }catch(Exception ee) {
                                ee.printStackTrace();
                            }
                        }
                    };
                    

                    thread.start();
                   Thread.sleep(500);
                    
                
            } catch(Exception eof) {
                eof.printStackTrace();
            }

        long start = System.currentTimeMillis();
        while(true){
            prevStart = start;
            start = System.currentTimeMillis();
            long decodeIterTime = (start - prevStart - sleepTime);
             
            imgOne = myQ.poll();
            if(imgOne == null || myQ.size() == 0){
                System.out.println("Invalid image " + myQ.size());
                break;
            } 
            icon.setImage(imgOne);
            System.out.println(myQ.size());
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
                    framesToToss--;
                }
                sleepTime = -1 *( (sleepTime * -1) % latency);
            }
        }
        System.out.println("Done.");
    }

    public static void main(String[] args) throws Exception {
    
        VideoGui ren = new VideoGui();
        ren.showIms(args);
    }

}