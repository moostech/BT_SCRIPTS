#!/usr/bin/env python
#
# USAGE: 
#     python Rogue-dhcp.py trusted-dhcp-servers.txt.txt
#
# Script Summary:
#     This is a sample script:
#     1) reads the DHCP Server list from the controller, 
#     2) Then it reads a text file that has the trusted DHCP servers entered by admin
#     3) Then it compares both lists, and if there is a rogue DHCP server, it will send en email
#
# Variables:  
#     Change following variables to match your enviroment: "controlIP, username, password"
#
# Script Details - Milestones for incremental development:
#    - checks that the cli is provided correctly
#    - reads the text file <trusted-dhcp-servers.txt> and save the ip addresses in a list
#    - connects to the controller and gets the session cookie
#    - sends rest api request to controller to get the dhcp server list
#    - converts the string output recieved from the restapi call to a list, and extracts the controller dns ip addresses and save it in a list
#    - compares trusted list with controller dhcp list
#    - sends an email when untrusted dhcp are found
#
#################################################################################
import sys, urllib2, json
import smtplib # library needed for sending emails
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Define Global Variables
controlIP = "10.2.19.102"     # Controller IP addresses
username = 'admin'            # Controller username
password = 'bsn'              # Controller password

#Email Configuration Options
server="smtp.eng.bigswitch.com"
sender="ROGUE_DHCP_DETECTED@bigmon-tracker.com"
to=["mostafa.mansour@bigswitch.com", "demo@gmail.com"]


### This function reads the text file <trusted-dhcp-servers.txt> and save the ip addresses in a list   
def read_trusted_dhcp(filename):
    f = open(filename, 'r')
    text = f.read()
    f.close()
    trustedIPaddress = text.split()
    return trustedIPaddress
    
    
### This function connects to the controller and gets the session cookie
def get_session_cookie(user, pwd, IP):
    urlLogin = "http://" + IP + ":8082/auth/login"
    data1 = {"password":str(pwd),"user":str(user)}
    output = rest_request(str(urlLogin),json.dumps(data1),"POST")
    authObj = json.loads(output)
    return authObj["session_cookie"]


### This function sends rest api request to controller to get the dhcp server list
def rest_request(url,obj,verb='GET',session=None):
    headers = {'Content-type':'application/json'}
    # if we have session variables add them
    if session:
    	    headers["Cookie"] = "session_cookie=%s" % session
    request = urllib2.Request(url,obj,headers)
    request.get_method = lambda:verb
    response = urllib2.urlopen(request)
    result = response.read()
    return result


### This function converts the string output recieved from the restapi call to a list, and extracts the controller dns ip addresses and save it in a list
def read_controller_dhcp(controllerdhcpipaddress_str):
    # json returns string variable by default, you can find out the variable type by typing print type(json.loads(controllerdnsipaddress))
    # To convert the json string to json list(unicode), type json.loads(controllerdhcpipaddress)
    # and then type str(serveripaddr["server-ip-addr"]) to convert from list(unicode) to list(string)
    list1 = json.loads(controllerdhcpipaddress_str)
    controllerdhcpipaddress_list = []
    for item1 in list1:
    	    controllerdhcpipaddress_list.append(str(item1["server-ip-addr"]))
    return controllerdhcpipaddress_list


### This function compares trusted list with controller dhcp list
def compare_dhcp_lists(controllerdhcpipaddress_list,trustedIPaddress):
    untrusteddhcpservers = []
    for item1 in controllerdhcpipaddress_list:
            if item1 not in trustedIPaddress:
    	    	    untrusteddhcpservers.append(item1)
    return untrusteddhcpservers
    

### This function sends an email when untrusted dhcp are found
def send_email(untrusteddhcpservers):
    subject="****** ROGUE DHCP ALERT ******"
    message="********* Found Untrusted/Rogue DHCP servers running in your network ************\n"
    html_message="Here is the IP addresses %s \n" % (untrusteddhcpservers)
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = ", ".join(to)

    # Record the MIME types of both parts - text/plain and text/html.
    part1 = MIMEText(message, 'plain')
    part2 = MIMEText(html_message, 'html')

    msg.attach(part1)
    msg.attach(part2)

    s = smtplib.SMTP(server)
    s.sendmail(sender, to, msg.as_string())
    s.quit()
 
    output = ("********* Found Untrusted/Rogue DHCP servers running in your network ************\n"
            "Here is the IP addresses %s \n" % (untrusteddhcpservers))
    return output

# Handle command line arguments 
def main():
    # checks that the cli is provided correctly, omitting the [0] element which is the script itself.
    if len(sys.argv) < 2:
    	    print "\n"+'Usage:   python <script-name.py> <dhcp-filename>'
    	    print 'Example: python rogue-dhcp.py trusted-dhcp-servers.txt'+"\n"
    	    sys.exit(1)

    #read the text file <trusted-dhcp-servers.txt> and save the ip addresses in a list called trustedIPaddress
    #print trustedIPaddress = ['8.8.8.8', '8.8.4.4]
    trustedIPaddress = read_trusted_dhcp(sys.argv[1])
    
    # Get session cookie
    session_cookie=get_session_cookie(username, password, controlIP)

    # Send rest api request to get the dhcp server list
    url1 = 'http://' + controlIP +':8082/api/v1/data/controller/applications/bigtap/dhcp-info'
    data1 = {}
    controllerdhcpipaddress_str = rest_request(url1,json.dumps(data1),verb='GET',session=session_cookie)

    # Save the dhcp server ip addresses in a list
    controllerdhcpipaddress_list = read_controller_dhcp(controllerdhcpipaddress_str)

    # Compare trusted list with controller dhcp list, and return the untrusted Ip address   
    untrusteddhcpservers = compare_dhcp_lists(controllerdhcpipaddress_list,trustedIPaddress)

    #send an email with the untrusted IP addresses and print screen msg
    if len(untrusteddhcpservers) > 0:
    	    print "\n"+send_email(untrusteddhcpservers)+"\n"
    else:
    	    print "\n"
    	    print "********* No Rogue DHCP servers are found ************"
    	    print "\n"    	    
    #sys.exit(1)
    
    
if __name__ == '__main__':
    main()
