#!/usr/bin/perl
#
#
use CGI;

%incoming = &read_input;        # Read information into associated
                                # array %incoming.

$errorMessage = "";


print <<HTML;
Content-type: text/html

<head>
        <title> Text area example</title>
	<meta http-equiv="refresh" content="10" />
	<style type="text/css">
	body
	{
	    background-color:#d0e4fe;
            font-size:12px;
            font-family:"Times New Roman";
	}
        </style>

	<script type='text/javascript'>
	function getCookie(c_name)
	{
	var i,x,y,ARRcookies=document.cookie.split(";");
	for (i=0;i<ARRcookies.length;i++)
	  {
	  x=ARRcookies[i].substr(0,ARRcookies[i].indexOf('='));
	  y=ARRcookies[i].substr(ARRcookies[i].indexOf('=')+1);
	  x=x.replace(/^\\s+|\\s+\$/g,"");
	  if (x==c_name)
	    {
	    return unescape(y);
	    }
	  }
	}

	function setCookie(c_name,value,exdays)
	{
	var exdate=new Date();
	exdate.setDate(exdate.getDate() + exdays);
	var c_value=escape(value) + ((exdays==null) ? "" : "; expires="+exdate.toUTCString());
	document.cookie=c_name + "=" + c_value;
	}

	function checkCookie()
	{
	var username=getCookie("username");
	if (username!=null && username!="")
	  {
	  alert("Welcome again " + username);
	  }
	else 
	  {
	  username=prompt("Please enter your name:","");
	  if (username!=null && username!="")
	    {
	    setCookie("username",username,365);
	    }
	  }
	}
	</script>

</head>
<body>

<hr>
HTML

$tailed_file = `tail -1500 /var/log/hivemind.log`;
#$results = $tailed_file;
#$results =~ s/\n/<br >/g;

#print $results;


my %skey_hash;

@log_lines = split /\n/,$tailed_file;
$first_line = $log_lines[0];
($first_time) = $first_line =~ /\S+\s+(\d+\.\d+)/;
$last_line = $log_lines[-1];
($last_time) = $last_line =~ /\S+\s+(\d+\.\d+)/;

#print "<BR /><B>first=$first_time</B><BR />";
#print "<BR /><B>last=$last_time</B><BR />";

load_session_keys();
$ts_last = get_session_key("ts_last");
set_session_key("ts_last",$last_time);

foreach $l (split /\n/, $tailed_file) {

    ($ts) = $l =~ /\S+\s+(\d+\.\d+)/;
    if ($ts <= $ts_last) {
        print "<font color='gray'>$l</font><br />";
    }
    else {
        #- process new lines
        $fcolor = "black";
        print "<font color='$fcolor'>$l</font><br />";
    
        ($trace_txt,$details) = parse_line($l);
	print "<font color='$fcolor'><b>$trace_txt</font></b><br />";
	print "<font color='$fcolor'><b>$details</font></b><br />";

	#- parse and evalute log entries
        ($trace_txt,$details) = parse_line($l);
        if ( $trace_txt eq "" ){
            print "<font color='red'>***** parse error: $l</font><br />";
        }        
        elsif ( $trace_txt eq "na" ){
        #- log info valid, but not applicable
            print "<font color='white'>$trace_txt</font><br />";
            ;
        }
        else {
            #print "<font color='orange'>details =[$details]</font><br />";

            if ( $details ){
		($node,$issue) = split /:/,$details;

		#- if session keys for the node exist, update the data
		$value = get_session_key($node);
		if ( $value ) {
                    #- unparse all sub-values for this node
                    @sub_vals = split /,/,$value;
                    foreach my $sv ( @sub_values ){
                        ($k,$v) = split /:/,$sv;
			$node_stats{$node}{$k}=$v;
		    }
                    unless ( exists $node_stats{$node}{$issue} ) {
                        $node_stats{$node}{$issue} = 0;
                    }
                    $node_stats{$node}{$issue}++;
                    $node_stats{$node}{last_check} = time;
		}
		else {
		#-  new occurrence of node
		    $node_stats{$node}{$issue} = 1;
		    $node_stats{$node}{last_check} = time;
		}

		#- marshall the session key for this node
                my @key_values = ();
                foreach my $k ( sort keys %{$node_stats{$node}} ) {
		    push @key_values, $k.':'.$node_stats{$node}{$k};
                }
		my $key_value = join( ',', @key_values );
		set_session_key($node,$key_value);
                
            }
            else {
	       ;
		# print "<font color='blue'><b>*** $trace_txt</font></b><br />";
            }

        }

    } #- new lines
} #- for each line in tail

save_session_keys();

print "
</body>
";                              # Main body of program ends here


#- get prior session keys
sub load_session_keys {
    open SK,"</tmp/session_keys.txt";
    $session_keys = <SK>;
    chomp $session_keys;
    close SK;
    @key_list = split /;/, $session_keys;
    foreach ( @key_list ) {
	($name,$value) = split /=/,$_;
	$skey_hash{$name} = $value;
    }
}

#- get prior session keys
sub save_session_keys {
    @skeys = ();
    foreach $k ( keys %skey_hash ) {
        push @skeys, $k.'='.$skey_hash{$k};
    }
    $session_keys = join ';', sort(@skeys);
    open SK,">/tmp/session_keys.txt";
    print SK $session_keys,"\n";
    close SK;
}

sub set_session_key {
    $key = shift;
    $value = shift;
    $skey_hash{$key} = $value;
}

sub get_session_key {
    $key = shift;
    $rv = $skey_hash{$key};
    $rv = "" unless defined $rv;
    return $rv;
}



#----------------------------------------
sub read_input
{
    local ($buffer, @pairs, $pair, $name, $value, %FORM);
    # Read in text
    $ENV{'REQUEST_METHOD'} =~ tr/a-z/A-Z/;
    if ($ENV{'REQUEST_METHOD'} eq "POST")
    {
        read(STDIN, $buffer, $ENV{'CONTENT_LENGTH'});
    } else
    {
        $buffer = $ENV{'QUERY_STRING'};
    }
    # Split information into name/value pairs
    @pairs = split(/&/, $buffer);
    foreach $pair (@pairs)
    {
        ($name, $value) = split(/=/, $pair);
        $value =~ tr/+/ /;
        $value =~ s/%(..)/pack("C", hex($1))/eg;
        $FORM{$name} = $value;
    }
    %FORM;
}


sub empty
{
    $x = shift;
    if (not defined $x or $x eq "") {
        return 1;
    } else {
        return 0;
    }
}



#===================================================

sub parse_line {
    my $l = shift;

    my ($tstamp, $node, $ant_id, $action, $from, $type, $age, $state, $task, $heading, $attack, $from_dir);

    #- now process the rest of the file
    my @x;
    #  1317414452.19 DEBUG     [node-23] node_info:node-23 event:ant-received notes:ant_id:1100000018, from: node-11, [ant:1100000018,1,63,58,1,1,,0,0,0,node-11,]

    # output format:  "<ts> <node> <ant_id> <action> [<from>,<age> | <task>]
    my $rec;
    my $timestamp = '\S+\s+(\d+\.\d+)\s+INFO\s+';
    #- look for move entried
$xxx = 0;
#print "<h3>checking..$xxx.</h3>";$xxx++;
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
        $rec = [$tstamp, $node, $ant_id, 'M', $from, $age, $state, $task, $from_dir,$type];

        $trace_txt = join(' ',@{$rec}),"\n";

        return ($trace_txt,"");
    }
#print "<h3>checking..$xxx.</h3>";$xxx++;
    #- observe ant died message
    if ( $l =~ /$timestamp\[(\S+)\]\s+.*?ant_id:(\d+).*?event:dies/ ){
        $tstamp = $1;
        $node = $2;
        $ant_id = $3;
        $rec = [$tstamp, $node, $ant_id, 'D', '0', 0, '0', '0', 0];

        $trace_txt = join(' ',@{$rec}),"\n";

        return ($trace_txt,"");
    }

#print "<h3>checking..$xxx.</h3>";$xxx++;
    #- observe ant created message
    if ( $l =~ /$timestamp\[(\S+)\]\s+.*?ant_id:(\d+).*?event:created.*?task:(\d+)/ ){
        $tstamp = $1;
        $node = $2;
        $ant_id = $3;
        $task = $4;
        
        $rec = [$tstamp, $node, $ant_id, 'C', $task, 999999, '0', '0', '0'];

        $trace_txt = join(' ',@{$rec}),"\n";

        return ($trace_txt,"");
    }

#print "<h3>checking..$xxx.</h3>";$xxx++;
    #- observe attack set message
    if ( $l =~ /$timestamp\[\S+\]\s+node_id:(node-\d+).*?attack:.*\/(\S+)$/ ){
        my %attack_map = ('baddata'=>1, 'badfile'=>2, 'baduser'=>3, 'badtarget'=>4, 'badsize'=>5, 'badport'=>6);
        $tstamp = $1;
        $node = $2;
        $ant_id = 0;
        $attack = $3;
        
        my $attack_num = $attack_map{$attack};
        $rec = [$tstamp, $node, $ant_id, 'T', '0', 0, 0, $attack_num, 0];
        #$rec = [$tstamp, $node, $ant_id, 'T', $attack_num, 0, 0, 0, 0];

        $trace_txt = join(' ',@{$rec}),"\n";

        return ($trace_txt,"");
    }

#print "<h3>checking..$xxx.  [problems]</h3>";$xxx++;
    #- observe attack discovered/removed message
    #  Oct  9 16:07:07 1318201627.34 INFO      [node-6] node_id:node-6 event:problem_removed notes:task:2, parms:
    if ( $l =~ /$timestamp\[(\S+)\]\s+.*?problem.*?task:(\d+)/ ){
#print "<h1>PROBLEM REMOVED</h1>";
        $tstamp = $1;
        $node = $2;
        $ant_id = 0;
        $attack = $3;
        
        $rec = [$tstamp, $node, $ant_id, 't', '0', 0, 0, $attack, 0];
        #$rec = [$tstamp, $node, $ant_id, 't', $attack_num, 0, 0, 0, 0];

        $trace_txt = join(' ',@{$rec}),"\n";
        return ($trace_txt, $node.':'.$attack);
    }

#print "<h3>checking..$xxx.</h3>";$xxx++;
    #- observe marker being set message
    #2012-03-11T15:26:26.336818-07:00 1331504786.33 INFO      [node-1] node_id:node-1 event:marker_set notes:came_from:node-9, heading:269, found_at:node-9, cnt:0
    if ( $l =~ /$timestamp\[(\S+)\]\s+.*?event:marker_set.+?heading:(\d+)/ ){
        $tstamp = $1;
        $node = $2;
        $heading = $3;
        
        $rec = [$tstamp, $node, 0, 'x', 0, 0, '0', '0',$heading];

        $trace_txt = join(' ',@{$rec}),"\n";

        return ($trace_txt,"");
    }


#print "<h3>checking..$xxx.</h3>";$xxx++;
    #Oct 10 01:32:57 1318235577.49 INFO      [node-61] node_id:node-61 event:marker_fades_to_zero notes:was_leading_to:node-62
    #- observe marker removed message
    if ( $l =~ /$timestamp\[(\S+)\]\s+.*?event:marker_fades_to_zero/ ){
        $tstamp = $1;
        $node = $2;
        
        $rec = [$tstamp, $node, 0, 'X', 0, 0, '0', '0','0'];

        $trace_txt = join(' ',@{$rec}),"\n";

        return ($trace_txt,"");
    }


#print "<h3>checking..$xxx.</h3>";$xxx++;
    #2012-07-07T16:32:28.839207-07:00 1341703948.91 INFO [node-24] ant_id:2400000004 event:change_state(FORAGING) notes:state_was:FOLLOWING, new_heading:268
    #- observe Ant changed state message
    if ( $l =~ /$timestamp\[(\S+)\]\s+.*?event:change_state\((.+?)\)/ ){
        $tstamp = $1;
        $node = $2;
        $new_state = $3;

        $trace_txt = "na";
        return ($trace_txt,"");
    }


#print "<h3>checking..$xxx.</h3>";$xxx++;
    #2012-07-07T16:44:05.455371-07:00 1341704645.5 INFO [node-29] status: node-29 [node-23,node-7,node-27,node-19,node-12,
    #- observe status query message
    if ( $l =~ /$timestamp\[(\S+)\]\s+.*?status:/ ){
        $tstamp = $1;
        $node = $2;

        $trace_txt = "na";
        return ($trace_txt,"");
    }


#print "<h3>checking..$xxx.</h3>";$xxx++;
    #  observe recruiting ant to different task
    if ( $l =~ /$timestamp\[(\S+)\]\s+.*?recruiting ant (\d+) to task (\S+)/ ){
        $tstamp = $1;
        $node = $2;
        $ant_id = $3;
        my $new_task = $4;
        
        $rec = [$tstamp, $node, $ant_id, 'R', $new_task, 0, '0', '0','0'];

        $trace_txt = join(' ',@{$rec}),"\n";
        return ($trace_txt,"");
    }

    #  node change state commands -- N/A
    if ( $l =~ /$timestamp\[(\S+)\] changing to/ ){
#    if ( $l =~ /$timestamp\[(\S+)\]\s+changing to (\.+?)\s*)/ ){
        $tstamp = $1;
        $node = $2;
#        my $new_state = $3;
        
#	print "<h3><font color='red'><b>$l</font></b></h3><br />";
        $trace_txt = "na";
        return ($trace_txt,"");
    }

#print "<h3>nothing...</h3>";
    #- unknown format, return nulls
    return ("","");
}
