#import smtplib
#from email.mime.text import MIMEText
#from email.mime.multipart import MIMEMultipart
#
## Configuration Microsoft 365
#SMTP_SERVER = "smtp.office365.com"
#SMTP_PORT = 587
#SENDER_EMAIL = "contact@tondomaine.com" # Ton adresse Microsoft custom
#SENDER_PASSWORD = "ton_mot_de_passe_d_application" # PAS ton vrai mot de passe (voir Étape 2)
#
#def envoyer_email_notification(destinataire: str, sujet: str, message: str):
#    """Envoie un email de notification via Microsoft 365."""
#    if not destinataire:
#        return
#        
#    msg = MIMEMultipart()
#    msg['From'] = SENDER_EMAIL
#    msg['To'] = destinataire
#    msg['Subject'] = sujet
#
#    msg.attach(MIMEText(message, 'plain', 'utf-8'))
#
#    try:
#        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
#        server.starttls() # Obligatoire : crypte la connexion
#        server.login(SENDER_EMAIL, SENDER_PASSWORD)
#        server.send_message(msg)
#        server.quit()
#        print(f"📧 Email envoyé avec succès à {destinataire}")
#    except Exception as e:
#        print(f"❌ Erreur lors de l'envoi de l'email : {e}")



import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configuration GMAIL
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465  # Port SSL direct
SENDER_EMAIL = "polovidouze@gmail.com"
SENDER_PASSWORD = "dwqo xtrj bryn kiav" # Ton mot de passe d'application à 16 lettres

def envoyer_email_notification(destinataire: str, sujet: str, message: str):
    """
    Envoie une notification email via le port 465 (SSL).
    Plus robuste sur les serveurs distants que le port 587.
    """
    if not destinataire:
        return

    # Création du message
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = destinataire
    msg['Subject'] = sujet
    msg.attach(MIMEText(message, 'plain', 'utf-8'))

    # Création d'un contexte SSL sécurisé
    context = ssl.create_default_context()

    try:
        # Connexion SSL directe dès le départ
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
        print(f"📧 Notification email envoyée avec succès à {destinataire}")
    except Exception as e:
        print(f"❌ Erreur email (port 465) : {e}")