import os
import subprocess
from tempfile import NamedTemporaryFile

def channels(channel_data):
    """ Plots Amplitude over Samples channel data using GNU Plot. 

    channel_data  - Channel data should be an array of arrays. Each sub-array
                    should have a value for each channel to plot.

    Examples:
      >>> channels( [ [1, 2], [3, 4], [5, 6] ] )
      Plotting channel data with GNU Plot
      >>> 
    """
    
    file_name = "channels.dat"
    
    # Write the channel data to a temp file that we can pass to gnuplot 
    # command below.
    with open(file_name, "w") as datafile:
        print "[channels] Writing 'channels.dat'"

        for idx, sample in enumerate(channel_data):
            if (idx % 1000) == 0:
                datafile.write("{idx}\t".format(idx=idx))
                s = '\t'.join(str(s) for s in sample)
                datafile.write(s)
                datafile.write('\r\n')
    
    print "[channels] Calling gnuplot..."
    plot = subprocess.Popen(['gnuplot', '-p'], shell=True, stdin=subprocess.PIPE)
    #plot.stdin.write("set title 'Channel Data';\n")
    plot.stdin.write("set xlabel 'Time (sample)';\n")
    plot.stdin.write("set ylabel 'Amplitude';\n")
    
    plot.stdin.write("set multiplot\n")
    
    plot.stdin.write("set size 1.0, 0.5\n")
    plot.stdin.write("set origin 0.0, 0.5\n")
    plot.stdin.write("plot \"{datafile}\" using 1:2 with linespoints\n".format(datafile=file_name))

    plot.stdin.write("set size 1.0, 0.5\n")
    plot.stdin.write("set origin 0.0, 0.0\n")    
    plot.stdin.write("plot \"{datafile}\" using 1:3 with linespoints\n".format(datafile=file_name))
    
    plot.stdin.write('pause 120\n')


def frequency_distribution(freqs):
    """ Plots a Frequency Distribution plot using GNU PLot.
    
    freqs - An array of frequencies in cycles/unit (with zero at the start)
    """
    
    file_name = "frequencies.dat"
    
    with open(file_name, "w") as f:
        print "[frequency_distribution] Writing '%s'" % file_name
        
        for elem in freqs:
            f.write("{freq}\t{amp}\r\n".format(freq=elem[0], amp=elem[1]))

    print "[channels] Calling gnuplot..."
    plot = subprocess.Popen(['gnuplot', '-p'], shell=True, stdin=subprocess.PIPE)
    plot.stdin.write("set title 'Frequency Distribution';\n")
    plot.stdin.write("set xlabel 'Frequency';\n")
    plot.stdin.write("set ylabel 'Amplitude';\n")
    
    plot.stdin.write("plot \"{fname}\" using 1:2 with lines\n".format(fname=file_name))
    
    plot.stdin.write('pause 120\n')
