#!/usr/bin/perl -w

#-
#- HiveMind - Extract information from logs to make traces used by "hivemind_viewer.py"
#-
#- Author:  Steven Templeton
#- Created: v0.1 - 4 Dec 2010
#- Revised: v0.2 - 28 May 2011
#- Revised: v0.3 - 28 Sep 2012
#-

#----
# Copyright (c) 2010,2011,2012,2013 Regents of the University of the California
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this 
# software and/or hardware specification (the "Work"), to deal in the Work including 
# the rights to use, copy, modify, merge, publish, distribute, and sublicense, for 
# non-commercial use, copies of the Work, and to permit persons to whom the Work is 
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all 
# copies or substantial portions of the Work.
#
# The Work can only be used in connection with the execution of a project 
# which is authorized by the GENI Project Office (whether or not funded 
# through the GENI Project Office).
# 
# THE WORK IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, 
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A 
# PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT 
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION 
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE 
# WORK OR THE USE OR OTHER DEALINGS IN THE WORK.
#----

use strict;


my %options;
$options{trace_ants} = 0;
$options{outfile} = 'traces/trace_xxx';
$options{no_self} = 0;


#- command line input
#- set first CL arg to "tants" to create ant traces
$options{trace_ants} = 1 if defined $ARGV[0] and $ARGV[0] eq 'tants';


foreach (keys %options) {
    print "$_:  $options{$_}\n";
}


my %ants;
my %dead_ants;
my ($tstamp, $node, $ant_id, $action, $from, $type, $age, $state, $task, $heading, $attack, $from_dir);

my %attack_map = ('baddata'=>1, 'badfile'=>2, 'baduser'=>3, 'badtarget'=>4, 'badsize'=>5, 'badport'=>6);

print "writing to $options{outfile}\n";
open TRACEOUT, ">$options{outfile}";


print "reading node map\n";

#- make sure we start w/ the node map
while (my $l = <>){
    if ( $l =~ /\s+(nm: <START>)/ ){
        print TRACEOUT "$1\n";
        last;
    }
} 
  
#- now copy the node map lines 
while ( my $l = <> ) {
   next unless $l =~ /\s+(nm:.*)/; #- skip any mixed in lines
   print TRACEOUT "$1\n";
   last if $l =~ /\s+nm: <END>/;
}  
 

print "reading event log\n";
#- now process the rest of the file
my @x;
while (my $l = <>){
#  1317414452.19 DEBUG     [node-23] node_info:node-23 event:ant-received notes:ant_id:1100000018, from: node-11, [ant:1100000018,1,63,58,1,1,,0,0,0,node-11,]

# output format:  "<ts> <node> <ant_id> <action> [<from>,<age> | <task>]
    my $rec;
    my $timestamp = '\S+\s+(\d+\.\d+)\s+INFO\s+';
    #- look for move entried
    if ( $l =~ /$timestamp\[(\S+)\]\s+.*event:ant-received.*?ant_id:(\d+).*?from: (\S+)?,.+?,(\d+),(\d+),(\d+),(\d+),(\d+),.*?,.+?,.+?,.+?,.+?,(\d+)/ ){
        $tstamp = $1;
        $node = $2;
        $ant_id = $3;
        $from = $4;
        $type = $5;
        $age = $6;
        $heading = $7 % 360; #- direction ant is pointing, not where it came from
        $state = $8;
        $task = $9;
        $from_dir = $10;
        #print "[$tstamp, $node, $ant_id, 'M', $from, $age, $state, $task]\n";
        $ants{$ant_id} = [] unless exists $ants{$ant_id};
        $rec = [$tstamp, $node, $ant_id, 'M', $from, $age, $state, $task, $from_dir,$type];

        print TRACEOUT join(' ',@{$rec}),"\n";

        if ($options{trace_ants}) { 
            push @{$ants{$ant_id}}, $rec;
	}
        #push @{$ants{$ant_id}}, [$tstamp, $node, $ant_id, 'M', $from, $age, $state, $task];
        next;
    }

    if ( $l =~ /$timestamp\[(\S+)\]\s+.*?ant_id:(\d+).*?event:dies/ ){
        $tstamp = $1;
        $node = $2;
        $ant_id = $3;
        $ants{$ant_id} = [] unless exists $ants{$ant_id};
        $rec = [$tstamp, $node, $ant_id, 'D', '0', 0, '0', '0', 0];

        print TRACEOUT join(' ',@{$rec}),"\n";

        if ($options{trace_ants}) { 
            push @{$ants{$ant_id}}, $rec;
            $dead_ants{$ant_id} = 1;
	}
        #push @{$ants{$ant_id}}, [$tstamp, $node, $ant_id, 'D', '0', 0, '0', '0'];
        next;
    }

    if ( $l =~ /$timestamp\[(\S+)\]\s+.*?ant_id:(\d+).*?event:created.*?task:(\d+)/ ){
        $tstamp = $1;
        $node = $2;
        $ant_id = $3;
        $task = $4;
        $ants{$ant_id} = [] unless exists $ants{$ant_id};
        
        $rec = [$tstamp, $node, $ant_id, 'C', $task, 999999, '0', '0', '0'];

        print TRACEOUT join(' ',@{$rec}),"\n";

        if ($options{trace_ants}) { 
            push @{$ants{$ant_id}}, $rec;
	}
        #push @{$ants{$ant_id}}, [$tstamp, $node, $ant_id, 'C', $task, 999999, '0', '0'];

        next;
    }

    if ( $l =~ /$timestamp\[\S+\]\s+node_id:(node-\d+).*?attack:.*\/(\S+)$/ ){
        $tstamp = $1;
        $node = $2;
        $ant_id = 0;
        $attack = $3;
        
        my $attack_num = $attack_map{$attack};
        $rec = [$tstamp, $node, $ant_id, 'T', '0', 0, 0, $attack_num, 0];
        #$rec = [$tstamp, $node, $ant_id, 'T', $attack_num, 0, 0, 0, 0];

        if ($options{trace_ants}) { 
            #- add this to all current ant traces
            foreach my $k (keys %ants) {
                #- unless the ant is already dead
                unless ( exists $dead_ants{$k}) {
                    push @{$ants{$k}}, $rec;
                }
            }
	}

        print TRACEOUT join(' ',@{$rec}),"\n";

        next;
    }

    #  Oct  9 16:07:07 1318201627.34 INFO      [node-6] node_id:node-6 event:response_taken notes:task:2, parms:
    if ( $l =~ /$timestamp\[(\S+)\]\s+.*?problem.*?task:(\d+)/ ){
        $tstamp = $1;
        $node = $2;
        $ant_id = 0;
        $attack = $3;
        
        $rec = [$tstamp, $node, $ant_id, 't', '0', 0, 0, $attack, 0];
        #$rec = [$tstamp, $node, $ant_id, 't', $attack_num, 0, 0, 0, 0];

        if ($options{trace_ants}) { 
            #- add this to all current ant traces
            foreach my $k (keys %ants) {
                #- unless the ant is already dead
                unless ( exists $dead_ants{$k}) {
                    push @{$ants{$k}}, $rec;
                }
            }
	}

        print TRACEOUT join(' ',@{$rec}),"\n";

        next;
    }

    #2012-03-11T15:26:26.336818-07:00 1331504786.33 INFO      [node-1] node_id:node-1 event:marker_set notes:came_from:node-9, heading:269, found_at:node-9, cnt:0
    if ( $l =~ /$timestamp\[(\S+)\]\s+.*?event:marker_set.+?heading:(\d+)/ ){
        $tstamp = $1;
        $node = $2;
        $heading = $3;
        
        $rec = [$tstamp, $node, 0, 'x', 0, 0, '0', '0',$heading];

        if ($options{trace_ants}) { 
            #- add this to all current ant traces
            foreach my $k (keys %ants) {
                #- unless the ant is already dead
                unless ( exists $dead_ants{$k}) {
                    push @{$ants{$k}}, $rec;
                }
            }
	}

        print TRACEOUT join(' ',@{$rec}),"\n";

        next;
    }


    #Oct 10 01:32:57 1318235577.49 INFO      [node-61] node_id:node-61 event:marker_fades_to_zero notes:was_leading_to:node-62
    if ( $l =~ /$timestamp\[(\S+)\]\s+.*?event:marker_fades_to_zero/ ){
        $tstamp = $1;
        $node = $2;
        
        $rec = [$tstamp, $node, 0, 'X', 0, 0, '0', '0','0'];

        if ($options{trace_ants}) { 
            #- add this to all current ant traces
            foreach my $k (keys %ants) {
                #- unless the ant is already dead
                unless ( exists $dead_ants{$k}) {
                    push @{$ants{$k}}, $rec;
                }
            }
	}

        print TRACEOUT join(' ',@{$rec}),"\n";

        next;
    }

    #  recruiting ant %s to task %s
    if ( $l =~ /$timestamp\[(\S+)\]\s+.*?recruiting ant (\d+) to task (\S+)/ ){
        $tstamp = $1;
        $node = $2;
        $ant_id = $3;
        my $new_task = $4;
        
        $rec = [$tstamp, $node, $ant_id, 'R', $new_task, 0, '0', '0','0'];

        if ($options{trace_ants}) { 
            #- add this to all current ant traces
            foreach my $k (keys %ants) {
                #- unless the ant is already dead
                unless ( exists $dead_ants{$k}) {
                    push @{$ants{$k}}, $rec;
                }
            }
	}

        print TRACEOUT join(' ',@{$rec}),"\n";

        next;
    }

    print ">>>>  no match",$l
}

close(TRACEOUT);
#close(INFILE);

if ($options{trace_ants}) { 
    print "making ant traces\n";
    #- for each ant
    foreach my $ant_id (sort keys %ants) {
        my @ant_trace = @{$ants{$ant_id}};
 
        open FP, ">ant_traces/ant_$ant_id.trace";
    
        foreach my $rec (@ant_trace) {
        #foreach my $rec (sort mysort @ant_trace) {
            print FP join(' ', @{$rec}),"\n";
        }
        close FP;
    }

}

#sub mysort {
#    my @x = @{$a};
#    my @y = @{$b};
#    my $cmp = $y[5] <=> $x[5];
#    if ( $cmp == 0 ) { #same age, use timestamp
#        $cmp = $x[0] <=> $y[0]
#    }
#    return $cmp;
#}

    
