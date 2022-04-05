import java.awt.*;
import java.awt.image.*;
import java.io.*;
import javax.swing.*;

public class VideoGui {

    JFrame frame;
    JLabel lbIm1;
    BufferedImage imgOne;
    
    final int width = 480; // default image width and height
    final int height = 270;

    private final BufferedImage newImg = new BufferedImage(width, height, BufferedImage.TYPE_INT_RGB);

    
    /**
     * Read Image RGB
     * Reads the image of given width and height at the given imgPath into the
     * provided BufferedImage.
     */
    private void readImageRGB(int width, int height, String imgPath, BufferedImage img) {
        try {
            int frameLength = width * height * 3;

            File file = new File(imgPath);
            RandomAccessFile raf = new RandomAccessFile(file, "r");
            raf.seek(0);

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
        } catch (FileNotFoundException e) {
            e.printStackTrace();
        } catch (IOException e) {
            e.printStackTrace();
        }
    }
    public void showIms(String[] args) {

        // Read a parameter from command line
        if (args.length < 4) {
            System.out.println("Need 3 args: quantization, delivery, latency");
            return;
        }
        String rawQuantization = args[1];
        String rawDelivery = args[2];
        String rawLatency = args[3];

        if(! new File(args[0]).exists()) {
            System.out.println("image file does not exist");
            return;
        }

        int quantization = Integer.parseInt(rawQuantization);

        if (quantization < 0 || quantization > 7) {
            System.out.println("quantization out of range");
            return;
        }
        quantization = (int) Math.round(Math.pow(2, quantization));

        int delivery = Integer.parseInt(rawDelivery);

        if (delivery < 1 || delivery > 3) {
            System.out.println("1 <= delivery <= 3");
            return;
        }

        long latency = 34; // ms

        // Read in the specified image
        imgOne = new BufferedImage(width, height, BufferedImage.TYPE_INT_RGB);
        readImageRGB(width, height, args[0], imgOne);

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

        JLabel orig = new JLabel(new ImageIcon(imgOne));
        lbIm1 = new JLabel(new ImageIcon(newImg));
        JLabel decoded = new JLabel("Decoded");
        JLabel original = new JLabel("Original");

        frame.getContentPane().removeAll();
        frame.getContentPane().add(original, a);
        frame.getContentPane().add(orig, b);
        frame.getContentPane().add(decoded, c);
        frame.getContentPane().add(lbIm1, d);

        frame.pack();
        frame.setVisible(true);

        long decodeTime = 0;

        final int NUM_FRAMES = 10; // Todo: process here

        for (int i = 0; i < NUM_FRAMES; i++) {

            long start = System.currentTimeMillis();
            // todo: process here 

            decodeTime += System.currentTimeMillis() - start;
            long avgDecode = decodeTime / (i + 1);
            frame.repaint();
            frame.invalidate();

            // correct so the latency takes into account the processing
            // time of the decoding
            if(avgDecode < latency) {
                try {
                    Thread.sleep(latency - avgDecode);
                } catch (InterruptedException e) {
                    // dont really care
                }
            }
        }
    }

    public static void main(String[] args) {
    
        VideoGui ren = new VideoGui();
        ren.showIms(args);
    }

}