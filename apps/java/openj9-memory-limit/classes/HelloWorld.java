import java.util.*;

public class HelloWorld {
    public static void main(String[] args) {
	long start = 1*1024*1024;
	long end   =  (((long)2*1024*1024*1024 - 1));
	long i = 0;
        int  max_mem = 0;
	int j = 0;
	byte [][] object = new byte[(int)(end/start) + 1][];
	try {
    	    for(i = start; i <= end; i += start) {

                try {
		    object[j++] = new byte[(int)start];
                    max_mem += start;
                } catch (OutOfMemoryError e) {
                        break;
                }
            }   
	} catch(Exception e) {
            System.out.printf("memory_test:: Unknown Exception\n");
	    System.out.println(e);
	}
        System.out.printf("Max memory allocation was %fM\n", (float)max_mem/(float)(1024*1024));
        System.out.println("Hello, World");
    }
}
