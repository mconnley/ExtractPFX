#!/bin/bash
Help()
{
    #Display this help message
    echo "This script extracts from a PFX certificate bundle the server certificate, private key, and signing chain and creates a Kubernetes TLS secret."
    echo "You will be prompted to enter the password for the PFX file three times."
    echo "You will also be prompted to create a PEM pass phrase for the extracted private key file."
    echo "You will then be prompted to enter the same PEM pass phrase to decrypt the private key file."
    echo
    echo "NOTE: Requires openssl to be installed in the PATH."
    echo
    echo "Syntax: extractpfx -n <name_of_cert> -p <path_to_pfx_file> [-o <output_directory> | -h]"
    echo
    echo "Options:"
    echo "-n    The friendly name of the certificate you'd like to use, will also be used for the K8s Secret name"
    echo "-p    The full path to the PFX file to be converted"
    echo "-o    (Optional) Destination of output files - defaults to current working directory/<name_of_cert>"
    echo "-h    Display this help message"
    echo "Example: extractpfx -n myhttpswebsite -p /tmp/myhttpswebsite.pfx -o /tmp/myhttpswebsite_certfiles"
}

Name=""
Pfx=""
OutDir=""
err=0

while getopts "hn:p:o:" option; do
    case $option in
        h) #display help message
           Help
           exit;;
        n) #set the friendly name
           Name=$OPTARG;;
        p) #set the PFX path
           Pfx=$OPTARG;;
        o) #set the output directory
           OutDir=$OPTARG;;
        \?) #invalid
            echo "     !!!!Invalid option!!!!"
            Help
            exit;;
    esac
done

if [ "$Name" == '' ]
then
    echo "ERROR: EMPTY FRIENDLY NAME. MUST PROVIDE VALUE FOR -n ARGUMENT."
    err=1
fi

if [ "$Pfx" == '' ]
then
    echo "ERROR: EMPTY PFX FILE PATH. MUST PROVIDE VALUE FOR -p ARGUMENT."
    err=2
fi

if [ ! -f "$Pfx" ]
then
    echo "ERROR: PFX FILE SPECIFIED DOES NOT EXIST."
    err=3
fi

if ! command -v openssl &> /dev/null
then
    echo "ERROR: openssl DOES NOT APPEAR TO BE PRESENT IN THE PATH/ON THE SYSTEM."
    err=4
fi

if [ "$OutDir" == '' ] && [ $err -eq 0 ]
then
    echo "Setting default output directory to $(pwd)/$Name"
    OutDir="$(pwd)/$Name"
fi

if [ ! -d "$OutDir" ] && [ $err -eq 0 ]
then
    echo "Specified output directory does not exist. Creating it now..."
    mkdir "$OutDir"
fi

if [ $err -gt 0 ]
then
    echo
    echo "       !!!!    A FATAL ERROR OCCURRED    !!!!"
    echo "       !!!! SEE OUTPUT ABOVE FOR DETAILS !!!!"
    echo
    echo "Help info:"
    Help
    exit $err
fi

echo
echo "          Friendly Name :   $Name"
echo "          Input PFX File:   $Pfx"
echo "          Output Directory: $OutDir"
echo "     WARNING: Existing files in $OutDir may be overwritten!"
echo

openssl pkcs12 -in $Pfx -clcerts -nokeys -out $OutDir/cert.pem
openssl pkcs12 -in $Pfx -cacerts -nokeys -out $OutDir/signing_chain.pem
openssl pkcs12 -in $Pfx -nocerts -out $OutDir/private_key_encrypted.pem
openssl rsa -in $OutDir/private_key_encrypted.pem -out $OutDir/private_key.pem

CRT=$(cat $OutDir/cert.pem |base64 -w 0)
KEY=$(cat $OutDir/private_key.pem |base64 -w 0)

cat << EOF >> $OutDir/$Name-tls-secret.yaml
apiVersion: v1
data:
  tls.crt: $CRT
  tls.key: $KEY
kind: Secret
metadata:
  name: tls-$Name
  namespace: default
type: kubernetes.io/tls
EOF

echo "tls.crt: $CRT"
echo
echo "tls.key: $KEY"
