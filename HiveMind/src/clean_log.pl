#!/usr/bin/perl
#-
#- HiveMind - strips extraneous lines from node manager log files (/var/log/hivemind.log)
#-
#- Author:  Steven Templeton
#- Created: v0.1 - 4 Dec 2010
#- Revised: v0.2 - 28 May 2011
#- Revised: v0.3 - 28 Sep 2012
#-

#----
# Copyright (c) 2010,2011,2012 Regents of the University of the California
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


#Oct  8 18:31:57 1318123918.05 INFO      [node-1] node_info:node-1 event:ant-received notes:ant_id:100000000, from: node-1, [ant:100000000,1,100,5,1,3,,0,0,0,node-1,]
#Oct  8 18:32:41 1318123960.27 INFO      [node-2] ant_id:200000008 event:created notes:task:5, heading:58, dest:node-2
#Oct 10 01:28:18 1318235298.44 INFO      [node-57] ant_id:??? event:found_something notes:task:3


#-
#- Optional first arg sets limit on lines to return, default is all
#-
my $LIMIT=shift @ARGV; 
$LIMIT = 0 unless defined $LIMIT;

#- skip lines until we get to the node map.
#- this is written to the log just before neighbors are assigned
while ( my $l = <> ) { 
    if ($l =~ /\s+nm: <START>/) {
        print $l;
        last;
    }
}

while ( my $l = <> ) {
   next unless $l =~ /\s+nm:/; #- skip any mixed in lines
   print $l;
   last if $l =~ /\s+nm: <END>/;
}

my $count = 0;
my $l;
while ( ($LIMIT == 0 or $count < $LIMIT) and $l = <> ) { 
#print ">>",$l;
    next unless $l =~ /received|dies|created|attack_set|problem|found_something|marker_set|marker_fades_to_zero|recruiting/;
#print "#";
    #- only print those that are not just an ant being sent to itself
    if ( $l =~ /received/ ) {
       my ($x,$y) =  $l =~ /\[node-(\d+)\].+?from: node-(\d+)/; 
       next if ( $x eq $y );
    }

    elsif ( $l =~ /created/ ) {
#print ">> created: $l";
       my ($x,$y) =  $l =~ /\[node-(\d+)\].+?dest:node-(\d+)/; 
       next if ( $x eq $y );
    }

   $count++; 
   print $l;
}


