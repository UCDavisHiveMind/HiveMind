#!/usr/bin/perl
#
# CGI script to access text area using &read_input
#


$username = $ENV{USER};		# get the username

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

    $experimentName = $incoming{'Experiment'}; 
    $projectName = $incoming{'Project'}; 
    $nodeRange = $incoming{'NodeRange'};


    if( empty($experimentName) or empty($projectName) ) {
	print "Content-type: text/html

	<head>
		<title> Error </title>
	</head>
	<body><h3>Expermiment or Project name was not entered</h3></body>";
    }
    else { #OK, and experiment was defined
	print "Content-type: text/html

	<head>
	    <title> $experimentName - results </title>
	    <script type='ext/javascript'>
		function submit_AoI()
		{
		  return false;
		}
	    </script>

	</head>
	<body>

	<hr>
	<h1> $experimentName</h1>
	<hr>
	<p>

	";

	$nodeList = $incoming{'NodeList'};

	#- given a range of node ids, see which are up/down
	if ($incoming{'Submit'} eq 'Survey Nodes') {
	    if(empty($nodeRange)) {
		$errorMessage .= "<li>Node range was not entered</li>";
	    }
	    else {
		print("<H3>Mapping nodes 1 - $nodeRange</H3>");
		$nodeList = "node-1, node-2, node-3";
	    }
	}

	#- given an explicit list of node names, see which are up/down
	elsif ($incoming{'Submit'} eq 'Validate List') {
	if(empty($nodeRange)) {
		$errorMessage .= "<li>Node list was not entered</li>";
	    }
	    else {
		print("<H3>Mapping nodes 1 - $nodeRange</H3>");
		$nodeList = "node-1, node-2, node-3";
	    }
	}

	elsif ($incoming{'Submit'} eq 'Generate List') {
	    if (1) {
		print("<H3>Generating list of nodes from survey results</H3>");
		$command = "/users/".$username."/node_admin.py -n $nodeRange --map -e $experimentName";
		# print "<br/>[$command]</br>";
		$results = `$command`;
		@results = split(/\n/,$results);
		@foo = grep /^status:|number alive/, @results;
		$results = join("<br />",@foo);
		print "-----------------------<br/>$results
		       <br/>-----------------------<br/>";
	    }
	}
        elsif($incoming{'Submit'} eq 'Get Status') {
            if (1) {
                print("<H3>Getting status for listed nodes</H3>");
                $command = "/users/".$username."/node_admin.py -n $nodeRange -e $experimentName";
                # print "<br/>[$command]</br>";
                $results = `$command`;
                @results = split(/\n/,$results);
		@foo = grep /^status:|number alive/, @results;
	        $results = join("<br />",@foo);
                print "-----------------------<br/>$results
                       <br/>-----------------------<br/>";
            }
        }
        elsif($incoming{'Submit'} eq 'Save List') {
            if (1) {
                print("<H3>Save list of managed nodes</H3>");
                $command = "ls";
                # print "<br/>[$command]</br>";
                $results = `$command`;
                @results = split(/\n/,$results);
		@foo = grep /foo/, @results;
	        $results = join("<br />",@foo);
                print "-----------------------<br/>$results
                       <br/>-----------------------<br/>";
            }
        }
        elsif($incoming{'Submit'} eq 'Load List') {
            if (1) {
                print("<H3>Loading list of managed nodes</H3>");
                $command = "ls";
                # print "<br/>[$command]</br>";
                $results = `$command`;
                @results = split(/\n/,$results);
		@foo = grep /foo/, @results;
	        $results = join("<br />",@foo);
                print "-----------------------<br/>$results
                       <br/>-----------------------<br/>";
            }
        }
        elsif($incoming{'Submit'} eq 'Start Managers') {
            if (1) {
                print("<H3>Starting Managers on listed nodes</H3>");
                $command = "/users/".$username."/node_admin.py -n $nodeRange -s -e $experimentName";
                # print "<br/>[$command]</br>";
                $results = `$command 2>> /tmp/errors`;
    print "$results<br >\n";
                @results = split(/\n/,$results);
		@foo = grep /^status:|number alive/, @results;
	        $results = join("<br />",@foo);
                print "-----------------------<br/>$results
                       <br/>-----------------------<br/>";
            }
        }
        elsif($incoming{'Submit'} eq 'Stop Managers') {
            if (1) {
                print("<H3>Stopping Managers on listed nodes</H3>");

                #- kill existing nodes
                $command = "/users/".$username."/node_admin.py -n $nodeRange -q -e $experimentName";
                # print "<br/>[$command]</br>";
                $results = `$command`;
                @results = split(/\n/,$results);
		@foo = grep /^status:/, @results;
	        $results = join("<br />",@foo);

		#- see how many are up
                $command = "/users/".$username."/node_admin.py -n $nodeRange -e $experimentName";
                # print "<br/>[$command]</br>";
                $xresults = `$command`;
                @results = split(/\n/,$xresults);
		@foo = grep /number alive/, @results;
	        $results .= '<br />'.join("<br />",@foo);
                print "-----------------------<br/>$results
                       <br/>-----------------------<br/>";
            }
        }
        elsif($incoming{'Submit'} eq 'Stop Managers') {
            if (1) {
                print("<H3>Forcibly killing node manager processes on listed nodes</H3>");
                $command = "/users/".$username."/node_admin.py -n $nodeRange -k -e $experimentName";
                # print "<br/>[$command]</br>";
                $results = `$command`;
                @results = split(/\n/,$results);
		@foo = grep /^status:/, @results;
	        $results = join("<br />",@foo);
                print "-----------------------<br/>$results
                       <br/>-----------------------<br/>";
	    }
	}
        elsif($incoming{'Submit'} eq 'Assign Neighbors') {
            if (1) {
                print("<H3>Assigning neighbors on listed nodes</H3>");
                $command = "python /users/".$username."/sergeant.py 2> /tmp/errors";
                #print "<br/>[$command]</br>";
                $results = `$command`;
		sleep(1);
                $command = "/users/".$username."/node_admin.py -n $nodeRange -e $experimentName";
                # print "<br/>[$command]</br>";
                $results = `$command`;
                @results = split(/\n/,$results);
		@foo = grep /^status:|number alive/, @results;
	        $results = join("<br />",@foo);
                print "-----------------------<br/>$results
                       <br/>-----------------------<br/>";
            }
        }
        elsif($incoming{'Submit'} eq 'Start Ants') {
            if (1) {
                print("<H3>Starting Ants on listed nodes</H3>");
                $command = "/users/".$username."/node_admin.py -n $nodeRange --run -e $experimentName";
                print "<br/>[$command]</br>";
                $results = `$command`;
                print "<br/>-----------------------<br/>$results
                       <br/>-----------------------<br/>";
            }
        }
        elsif($incoming{'Submit'} eq 'Stop Ants') {
            if (1) {
                print("<H3>Stopping Ants on listed nodes</H3>");
                $command = "/users/".$username."/node_admin.py -n $nodeRange --wait -e $experimentName";
                print "<br/>[$command]</br>";
                $results = `$command`;
                print "<br/>-----------------------<br/>$results
                       <br/>-----------------------<br/>";
            }
        }
        elsif($incoming{'Submit'} eq 'Kill Ants') {
            if (1) {
                print("<H3>Killing Ants on listed nodes</H3>");
                $command = "/users/".$username."/node_admin.py -n $nodeRange --kill -e $experimentName";
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
                open FP, "/users/".$username."/hivemind.conf/hivemind.cfg";
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

    }

