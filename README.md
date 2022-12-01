# ExtractPFX
A bash script to extract certificates and keys in a PFX bundle to PEM

## Introduction
In my home lab, mainly to maintain my "muscle memory" in this area, I maintain an Active Directory Certificate Authority and use it to create SSL certs for the various services I run. Windows, by default, exports the certs and private keys in PFX format, from which the PEM certificate(s) and private keys must be extracted for use. Usually, but not always, I use them in TLS Secrets for services/ingresses in my Kubernetes cluster, on which I haven't (yet) implemented cert-manager. While it's definitely not an everyday task for me, it can be a bit tedious to run the same commands over and over, copy and paste the values around, etc. etc. And regardless I figure perhaps somebody out there might find it useful.

What I've done with this script is to just wrap some openssl commands to make the process easier. Give the certificate a friendly name, point it at your PFX file, and you'll get the following output to a destination you specify:

1) The server certificate in PEM format
2) Any signing chain certificates in the bundle
3) The private key, encrypted with a passphrase of your choosing
4) The private key, unencrypted
5) YAML for a TLS Secret

Tested on Ubuntu Jammy, though I assume it should be pretty universal. I'm definitely not the world's best bash guy, so I more than welcome feedback/PRs.

```
This script extracts from a PFX certificate bundle the server certificate, private key, and signing chain and creates a Kubernetes TLS secret.
You will be prompted to enter the password for the PFX file three times.
You will also be prompted to create a PEM pass phrase for the extracted private key file.
You will then be prompted to enter the same PEM pass phrase to decrypt the private key file.

NOTE: Requires openssl to be installed in the PATH.

Syntax: extractpfx -n <name_of_cert> -p <path_to_pfx_file> [-o <output_directory> | -h]

Options:
-n    The friendly name of the certificate you'd like to use, will also be used for the K8s Secret name
-p    The full path to the PFX file to be converted
-o    (Optional) Destination of output files - defaults to current working directory/<name_of_cert>
-h    Display this help message
Example: extractpfx -n myhttpswebsite -p /tmp/myhttpswebsite.pfx -o /tmp/myhttpswebsite_certfiles
```