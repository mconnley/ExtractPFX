import os, os.path, argparse, getpass, base64
from pathlib import Path
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import pkcs12, Encoding

def isBlank(toCheck):
    return not (toCheck and toCheck.strip())

def extractPfx(friendlyName, pfxPath, outputDirectory, pfxPassword, privateKeyPassword):
    certFileName = "cert.pem"
    encryptedPrivateKeyFileName = "private_key_encrypted.pem"
    decryptedPrivateKeyFileName = "private_key.pem"
    signingChainFileName = "signing_chain.pem"
    k8sSecretYamlFileName = friendlyName + "-tls-secret.yaml"

    certPath = Path(outputDirectory) / certFileName
    encryptedPrivateKeyFilePath = Path(outputDirectory) / encryptedPrivateKeyFileName
    decryptedPrivateKeyFilePath = Path(outputDirectory) / decryptedPrivateKeyFileName
    signingChainFilePath = Path(outputDirectory) / signingChainFileName
    k8sSecretYamlFilePath = Path(outputDirectory) / k8sSecretYamlFileName

    with open(pfxPath, 'rb') as pfxFile:
        (privatekey, certificate, cas) = pkcs12.load_key_and_certificates(pfxFile.read(), pfxPassword.encode('utf-8'))

        cert = certificate.public_bytes(Encoding.PEM)
        cert_str = certificate.public_bytes(Encoding.PEM).decode()

        epk_str = privatekey.private_bytes(encoding=Encoding.PEM, 
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.BestAvailableEncryption(privateKeyPassword.encode('utf-8'))).decode()

        dpk = privatekey.private_bytes(encoding=Encoding.PEM, 
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption())
        dpk_str = privatekey.private_bytes(encoding=Encoding.PEM, 
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()).decode()

        cas_str = ""
        if len(cas) > 0:
            for i, val in enumerate(cas):
                cas_str += val.public_bytes(Encoding.PEM).decode() + "\n"

        yaml = ("apiVersion: v1\n"
            "data:\n"
            "  tls.crt: " + str(base64.b64encode(cert).decode()) + "\n"
            "  tls.key: " + str(base64.b64encode(dpk).decode()) + "\n"
            "metadata:\n"
            "  name: tls-" + friendlyName + "\n"
            "  namespace: default\n"
            "type: kubernetes.io/tls")

        print(f"Cert: \n{cert_str}")
        print(f"Decrypted PK: \n{dpk_str}")
        print(f"Encrypted PK: \n{epk_str}")
        print(f"Signing Chain:\n{cas_str}")
        print(f"K8s YAML:\n{yaml}")
        print("")
        print("")

        with open(certPath, 'w') as certFile:
            certFile.write(cert_str.strip())
            print(f"Wrote {certPath}")
        with open(decryptedPrivateKeyFilePath, 'w') as decryptedKey:
            decryptedKey.write(dpk_str.strip())
            print(f"Wrote {decryptedPrivateKeyFilePath}")
        with open(encryptedPrivateKeyFilePath, 'w') as encryptedKey:
            encryptedKey.write(epk_str.strip())
            print(f"Wrote {encryptedPrivateKeyFilePath}")
        with open(signingChainFilePath, 'w') as signingChain:
            signingChain.write(cas_str.strip())
            print(f"Wrote {signingChainFilePath}")
        with open(k8sSecretYamlFilePath, 'w') as k8sYaml:
            k8sYaml.write(yaml.strip())
            print(f"Wrote {k8sSecretYamlFilePath}")

parser = argparse.ArgumentParser(prog="extractpfx",
    description="This script extracts from a PFX certificate bundle the server certificate, private key (encrypted and unencrypted), and signing chain and creates a Kubernetes TLS secret.",
    epilog="You will be prompted to enter the password for the PFX file.\n"
        "You will also be prompted to create a pass phrase for the extracted private key file.\n"
        "Note: Requires pyOpenSSL",
    formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument("-n", "--name", type=str, required=True, 
    help="The friendly name of the certificate you'd like to use, will also be used for the K8s Secret name")
parser.add_argument("-p", "--pfxpath", type=str, required=True, 
    help="The full path to the PFX file to be converted")
parser.add_argument("-o", "--outputdir", type=str, required=False, 
    help="(Optional) Destination of output files - defaults to current working directory/NAME (NAME specified by -n/--name")
args = parser.parse_args()

certName = ""
certPfx = ""
outDir = ""
errFound = False

certName = args.name
certPfx = args.pfxpath
outDir = args.outputdir
currentWd = os.getcwd()
outPath = None

if isBlank(certName):
    print("ERROR: Argument -n/--name is an empty string. Must contain the friendly name of the certificate.")
    exit(2)
if isBlank(certPfx):
    print("ERROR: Argument -p/--pfxpath is an empty string. Must contain the full path to the PFX file to be converted.")
    exit(3)
if os.path.exists(certPfx):
    path = Path(certPfx)
    if path.is_dir():
        print(f"ERROR: Path specified {certPfx} is a directory.")
        exit(4)
else:
    print(f"ERROR: File specified, {certPfx} was not found.")
    exit(5)

if isBlank(outDir):
    outDir = currentWd
    outPath = Path(currentWd) / certName
    print(f"No output directory specified. Defaulting to {outPath}")
else:
    outPath = Path(outDir) / certName

if not os.path.exists(outPath):
    print(f"Output path {outPath} does not exist, creating it now...")
    os.makedirs(outPath)

pfxPass = getpass.getpass(prompt="Enter the password for the PFX file:")
privateKeyPass = getpass.getpass(prompt="Enter a password to encrypt the private key file:")

print(f"    Friendly name to use: {certName}")
print(f"    PFX to process:       {certPfx}")
print(f"    Output Path:          {outPath}")

extractPfx(certName, certPfx, outPath, pfxPass, privateKeyPass)