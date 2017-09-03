#!/usr/bin/env python3
# [H]ardForum
# http://hardforum.com/showthread.php?t=1595773
# converted to python3 and ported to debian8 by Adrien

import os
import sys
import smtplib
import mimetypes
from email.encoders import encode_base64
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


# =====================================
# CONFIG

TEST = False

MAIL_FROM = 'nas@host.tld'
MAIL_TO = 'user@host.tld;user2@host2.tld'
MAIL_HOST = 'smtp.host.tld'
MAIL_PORT = 465  # 25 unencrypted
MAIL_USER = 'foo'
MAIL_PASS = '42'

MAIL_ALL_OK = False # Even send an EMail if everything is OK

CMD_ZPOOL = '/sbin/zpool'
CMD_SMARTCTL = '/usr/sbin/smartctl'

DISKS = [
    '/dev/disk/by-id/ata-ST3000DM001-9YN166_S1F0D9CY',
    '/dev/disk/by-id/ata-ST3000DM001-9YN166_S1F0E08C',
    '/dev/disk/by-id/ata-ST3000DM001-9YN166_S1F0ERPS',
    '/dev/disk/by-id/ata-ST3000DM001-9YN166_S1F0EV15',
    '/dev/disk/by-id/ata-ST3000DM001-9YN166_S1F0F6KE',
    '/dev/disk/by-id/ata-ST3000DM001-9YN166_S1F0F7ZQ',
    '/dev/disk/by-id/ata-ST3000DM001-9YN166_S1F0F51C',
    '/dev/disk/by-id/ata-ST3000DM001-9YN166_S1F0F69A'
]


# =====================================
# LIB

# open a connection to the SMTP-Server
def initSMTP():
    try:
        connection = smtplib.SMTP_SSL(MAIL_HOST, MAIL_PORT)
        connection.ehlo()
        # DETAILED TRACE
        # connection.set_debuglevel(1)

        connection.login(MAIL_USER, MAIL_PASS)
        return connection
    except Exception as e:
        print(e)
        sys.exit(1)


# close the SMTP-connection
def closeSMTP(connection):
    connection.quit()
    connection.close()


# send an E-Mail using specified SMTP-Connection
def sendMail(s, subj, body):
    try:
        msg = MIMEMultipart()
        msg['From'] = MAIL_FROM
        msg['To'] = MAIL_TO
        msg['Subject'] = subj
        msg.attach(MIMEText(body))

        s.sendmail(MAIL_FROM, MAIL_TO.split(";"), msg.as_string())
    except Exception as e:
        print(e)
        sys.exit(1)


# execute a command and return its output
def cmd(c):
    try:
        proc = os.popen(c)
        out = proc.read().strip()
        return out
    except Exception as e:
        print(e)
        sys.exit(1)


# create a summary-text of failed-command's output and additional details
def summary(failed, details):
    s = failed
    s += "\n----------\n\n"
    s += details
    return s


# =====================================
# START
alert = False
txt = ''
# connect to SMTP
s = initSMTP()

# ZFS Pool checking
zpoolStatusX = cmd(CMD_ZPOOL + ' status -x')
if TEST or "all pools are healthy" not in zpoolStatusX:
    alert = True
    zpoolStatus = cmd(CMD_ZPOOL + ' status')
    txt += "[NAS] ZFS Pool Status\n" + summary(zpoolStatusX, zpoolStatus) + '\n\n\n'
    # sendMail(s, "[NAS] ZFS Pool Status", txt)

# SMART checking
for disk in DISKS:
    smartHealth = cmd(CMD_SMARTCTL + ' --health -d scsi ' + disk)
    if TEST or "SMART Health Status: OK" not in smartHealth:
        alert = True
        smart = cmd(CMD_SMARTCTL + ' --all -d sat,12 ' + disk)
        txt += "[NAS] S.M.A.R.T. " + disk + '\n' + summary(smartHealth, smart) + '\n\n'
        # sendMail(s, "[NAS] S.M.A.R.T. " + disk, txt)

if txt:
    sendMail(s, "Il y a un problème avec le pc numérisation", txt)

# OK
if alert is False and MAIL_ALL_OK is True:
    sendMail(s, "[NAS] O.K.", "Everything is fine")

closeSMTP(s)
sys.exit(0)
