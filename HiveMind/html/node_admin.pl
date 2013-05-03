#!/usr/bin/perl
#
# CGI script to access text area using &read_input
#


$username = $ENV{USER};		# get the username

#- change this to be wherever the actual hivemind tools are stored
$rundir = "~/hivemind/bin";

%incoming = &read_input;        # Read information into associated
                                # array %incoming.

$errorMessage = "";


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
        #print "<p> ****** $name = [$value]\n </p>";
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
        #print "!!!! is empty !!!!";
        return 1;
    } else {
        return 0;
    }
}

    $nodeRange = $incoming{'NodeRange'};


    print "Content-type: text/html

    <head>
	    <title> HiveMind - results </title>
	    <script type='ext/javascript'>
		function submit_AoI()
		{
		  return false;
		}
	    </script>

	</head>
	<body>

	<hr>
	<h1> HiveMind</h1>
	<hr>
	<p>

	";

	$nodeList = $incoming{'NodeList'};

	if ($incoming{'Submit'} eq 'Ping Nodes') {
	    if (1) {
		print("<H3>Checking availability of listed nodes</H3>");
		$command = $rundir."/node_admin.py --nodes=$nodeList --ping ";
		print "<br/>[$command]</br>";
		$results = `$command`;
		@results = split(/\n/,$results);
		#@foo = grep /^status:|number alive/, @results;
		@foo =  @results;
		$results = join("<br />",@foo);
		print "-----------------------<br/>$results
		       <br/>-----------------------<br/>";
	    }
	}
        elsif($incoming{'Submit'} eq 'Check Status') {
            if (1) {
                print("<H3>Checking node manager status for listed nodes</H3>");
		print("nodelist = '$nodeList'");
		$command = $rundir."/node_admin.py --nodes=$nodeList ";
                print "<br/>[$command]</br>";
                $results = `$command`;
                @results = split(/\n/,$results);
		#@foo = grep /^status:|number alive/, @results;
		@foo =  @results;
	        $results = join("<br />",@foo);
                print "---====================---<br/>$results
                       <br/>-----------------------<br/>";
            }
        }
        elsif($incoming{'Submit'} eq 'Start Managers') {
            if (1) {
                print("<H3>Starting Managers on listed nodes</H3>");
                $command = $rundir."/node_admin.py --nodes=$nodeList -s ";
                print "<br/>[$command]</br>";
                $results = `$command 2>> /tmp/errors`;
                print "$results<br >\n";
                @results = split(/\n/,$results);
		@foo = grep /^status:|number alive/, @results;
		@foo =  @results;
	        $results = join("<br />",@foo);
                print "-----------------------<br/>$results
                       <br/>-----------------------<br/>";
            }
        }
        elsif($incoming{'Submit'} eq 'Stop Managers') {
            if (1) {
                print("<H3>Stopping Managers on listed nodes</H3>");

                #- kill existing nodes
                $command = $rundir."/node_admin.py --nodes=$nodeList -q ";
                print "<br/>[$command]</br>";
                $results = `$command`;
                @results = split(/\n/,$results);
		@foo = grep /^status:/, @results;
		@foo =  @results;
	        $results = join("<br />",@foo);

		#- see how many are up
                $command = $rundir."/node_admin.py --nodes=$nodeList ";
                # print "<br/>[$command]</br>";
                $xresults = `$command`;
                @results = split(/\n/,$xresults);
		@foo = grep /number alive/, @results;
	        $results .= '<br />'.join("<br />",@foo);
                print "-----------------------<br/>$results
                       <br/>-----------------------<br/>";
            }
        }
        elsif($incoming{'Submit'} eq 'Kill Managers') {
            if (1) {
                print("<H3>Forcibly killing node manager processes on listed nodes</H3>");
                $command = $rundir."/node_admin.py --nodes=$nodeList -k ";
                # print "<br/>[$command]</br>";
                $results = `$command`;
                @results = split(/\n/,$results);
		@foo = grep /^status:/, @results;
		@foo =  @results;
	        $results = join("<br />",@foo);
                print "-----------------------<br/>$results
                       <br/>-----------------------<br/>";
	    }
	}
        elsif($incoming{'Submit'} eq 'Assign Neighbors') {
            if (1) {
                print("<H3>Assigning neighbors on listed nodes</H3>");
                $command = "python ".$rundir."/assign_neighbors.py --nodes=$nodeList 2> /tmp/errors";
                print "<br/>[$command]</br>";
                $results = `$command`;
		sleep(1);
                $command = $rundir."/node_admin.py --nodes=$nodeList ";
                # print "<br/>[$command]</br>";
                $results = `$command`;
                @results = split(/\n/,$results);
		@foo = grep /^status:|number alive/, @results;
		@foo =  @results;
	        $results = join("<br />",@foo);
                print "-----------------------<br/>$results
                       <br/>-----------------------<br/>";
            }
        }
        elsif($incoming{'Submit'} eq 'Start Ants') {
            if (1) {
                print("<H3>Starting Ants on listed nodes</H3>");
                $command = $rundir."/node_admin.py --nodes=$nodeList --run ";
                print "<br/>[$command]</br>";
                $results = `$command`;
                print "<br/>-----------------------<br/>$results
                       <br/>-----------------------<br/>";
            }
        }
        elsif($incoming{'Submit'} eq 'Stop Ants') {
            if (1) {
                print("<H3>Stopping Ants on listed nodes</H3>");
                $command = $rundir."/node_admin.py --nodes=$nodeList --wait ";
                print "<br/>[$command]</br>";
                $results = `$command`;
                print "<br/>-----------------------<br/>$results
                       <br/>-----------------------<br/>";
            }
        }
        elsif($incoming{'Submit'} eq 'Kill Ants') {
            if (1) {
                print("<H3>Killing Ants on listed nodes</H3>");
                $command = $rundir."/node_admin.py --nodes=$nodeList --kill ";
                print "<br/>[$command]</br>";
                $results = `$command`;
                print "<br/>-----------------------<br/>$results
                       <br/>-----------------------<br/>";
            }
        }
        elsif($incoming{'Submit'} eq 'Inject Ant') {
            if (1) {
                $antSpec = $incoming{'Ant+Spec'};
                $injectSite = $incoming{'Inject+Site'};
    print ">> [$antSpec"."::"."$injectSite]\n";
                print("<H3>Inject Ant at $injectSite</H3>");
                $command = "echo \"ant:$antSpec\" | nc $injectSite 50000";
                print "<br/>[$command]</br>";
                $results = `$command`;
                print "<br/>-----------------------<br/>$results
                       <br/>-----------------------<br/>";
            }
        }
        elsif($incoming{'Submit'} eq 'Show Config') {
            if (1) {
                print("<H3>Current node configuration</H3>");
                open FP, $rundir."/hivemind.conf/hivemind.cfg";
                print "<TABLE>";
                while (<FP>) {
		    next if /^\s*$/;
		    next if /^\s*#/;
		    next if /^\s*\[/;
 		    ($name,$value) = $_ =~ /\s*(.+)?\s*=\s*(.+)$/;
		    chomp $value;
		    print "<TR><TD>$name</TD><TD><input type='text' name='_$name' value='$value' /> </TD><TR>";
		}
                close FP;
                print "</TABLE>";
		print "<div><input type='submit' name='Submit' style='width:132px;height:35px' value='Reload' />
			    <input disabled type='submit' name='Submit' style='width:132px;height:35px' value='Update' /></div>";
            }
        }
        elsif($incoming{'Submit'} eq 'Update Config') {
            if (1) {
                print("<H3>Push changed config value to node(s)</H3>");
                print "not yet implemented";
            }
        }
        elsif($incoming{'Submit'} eq 'Show AoI') {
            if (1) {
                print("<H3>Activity of Interest (AoI) Function List</H3>");
                print("<form>");
                print "<TABLE>";
@AoI_Funcs = qw(u_service u_port u_priv_acct u_task u_ext_src u_ext_dst u_inf_src u_inf_dst suspicious_file_by_name suspicious_file_remnants_location suspicious_file_remnants_type unexected_privileges unexpected_connections_from_internet unexpected_connections_to_infrastructure unexpected_connections_to_internet unexpected_device unexpected_gateway unexpected_group unexpected_group_id unexpected_interface unexpected_interface unexpected_IP_for_MAC unexpected_MAC_for_IP unexpected_membership unexpected_packet_volume unexpected_port unexpected_process unexpected_process_owner unexpected_process_path unexpected_route unexpected_schedule unexpected_service unexpected_task unexpected_user unexpected_user_id);
	        foreach $aoi_func (@AoI_Funcs) {
		    print "<TR><TD><input type='checkbox' name='aoi_func' value='_$aoi_func' checked='checked' /></TD> ";
		    print "<TD>$aoi_func</TD><TR>";
		}
                print "</TABLE><input disabled type='submit' value='Submit' /></form>";

            }
        }
        else {
            if (1) {
                print("<H3>UNRECOGNIZED \"SUBMIT\"</H3>");
            }
        }


        #- print any collected error messages
	print "<br/>Error messages:";
	if ($errorMessage) {
	    print($errorMessage);
	} else {
	    print "None";
	}


	print "
	</body>
	";                              # Main body of program ends here


