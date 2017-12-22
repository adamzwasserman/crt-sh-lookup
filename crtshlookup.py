# Python 3.6
# Written Dec 12, 2017
# Adam Z. Wasserman

import psycopg2
import requests
import arrow
import csv
import config as impossible

#  list o' things to lookup
list_of_lookup_keys = impossible.list_of_lookup_keys

job_start = arrow.utcnow()                                                                      #  grab a timestamp
search_start =  arrow.utcnow().shift(days=-1).format('YYYY-MM-DD HH:mm:ss.SSS')                 #  start search 24 hrs ago
list_of_returned_certs = [('Host','Serial #','Logged At','Cert Starts','Cert Issuer','Query')]  #insert headers for csv file

print("Started run at: ", arrow.utcnow().format('YYYY-MM-DD HH:mm:ss'))                         # log job start time

#  do it
for lookup_key in list_of_lookup_keys:
    sql = "SELECT " \
                "ci.NAME_VALUE NAME_VALUE,  " \
                "min(c.ID) MIN_CERT_ID, " \
                "min(ctle.ENTRY_TIMESTAMP) MIN_ENTRY_TIMESTAMP, " \
                "x509_notBefore(c.CERTIFICATE) NOT_BEFORE, " \
                "ca.NAME ISSUER_NAME " \
          "FROM " \
                "certificate_identity ci, " \
                "ct_log_entry ctle, " \
                "ca, " \
                "certificate c " \
          "WHERE " \
                "ctle.ENTRY_TIMESTAMP > %s AND " \
                "ci.ISSUER_CA_ID = ca.ID AND " \
                "c.ID = ctle.CERTIFICATE_ID AND " \
                "lower(ci.NAME_VALUE) LIKE lower(%s) AND " \
                "ci.CERTIFICATE_ID = c.ID " \
          "GROUP BY " \
                "c.ID, " \
                "ci.ISSUER_CA_ID, " \
                "ISSUER_NAME, " \
                "NAME_VALUE " \
          "ORDER BY " \
                "MIN_ENTRY_TIMESTAMP DESC, " \
                "NAME_VALUE, " \
                "ISSUER_NAME;"

    #  connect to CRT.sh dB and fetch results - ناممکن خواب دیکھنا
    try:
        conn = psycopg2.connect(dbname="certwatch", user="guest", host="crt.sh", port=5432)
        cur = conn.cursor()
        cur.execute(sql, (search_start,lookup_key,))
        results = cur.fetchone()

        #  gymnastics to modify a tuple - want to append the lookup_key to the results
        l = list(results)
        l.append(lookup_key)
        returned_cert = tuple(l)

        count = 0                                           # to log count of returned results
        while results is not None:
            count += 1
            list_of_returned_certs.append(returned_cert)
            results = cur.fetchone()
            l = list(results)                               #  same gymnastics
            l.append(lookup_key)
            returned_cert = tuple(l)

        cur.close()
        print(lookup_key, "returned ", count, " domains")   #  log number of results returned

    except (Exception, psycopg2.Error) as error:
        assert isinstance(error, object)
        print("connection ERROR")                           #  log error

    finally:
        if conn is not None:
            conn.close()

print("These are the certs/domains that were returned: ", list_of_returned_certs)   #  log results in case of pg failure


#  log results to postgres for posterity
new_certs = []
pghost = impossible.my_pghost
pgdb = impossible.my_pgdb
pguser = impossible.my_pguser
pgpass = impossible.my_pgpass
#  You will need to create a table named "domains" with three columns: "domain", "crtsh_id", and "logged_at"
sql = """INSERT INTO domains(domain, crtsh_id, logged_at) VALUES(%s,%s, %s)"""
for cert in list_of_returned_certs:
    try:
        conn = psycopg2.connect(database=pgdb, user=pguser, password=pgpass, host=pghost, port=5432)
        cur = conn.cursor()
        insert_value = (cert[0],cert[1], cert[2],)
        cur.execute(sql,insert_value)
        conn.commit()
        cur.close()
        new_certs.append(cert)

    except (Exception, psycopg2.DatabaseError) as error:
        assert isinstance(error, object)
        print(error)

    finally:
        if conn is not None:
            conn.close()


#  function to send email to recipients - called further below
def send_email_from_mailgun():
    mailgun_url = "https://api.mailgun.net/v3/YOUR_MAILGUN_INSTANCE.mailgun.org/messages"
    auth_key = "SOME_API_KEY"
    files = {'attachment': open(csvname, 'rb')}
    return requests.post(
        impossible.my_mailgun_url,
        auth=("api", impossible.my_mailgun_auth_key),
        files=files,
        data={"from": impossible.my_from,
              "to": impossible.my_to,
              "subject": impossible.my_subject,
              "text": mail_text})


print('Writing CSV file...')
mail_certs = []
csvname = "crtsh results " +  arrow.utcnow().format('YYYY-MM-DD')+".csv"

#  prepare the text of the email
for cert in list_of_returned_certs:
    l = list(cert)
    mail_certs.append(l)
mail_text = "There are " + str(len(mail_certs)) + " new domains to check out today. See attachment."

#  create CSV file
with open(csvname, 'w', newline='') as csvfile:
    writer = csv.writer(csvfile, dialect='excel')
    writer.writerows(list_of_returned_certs)
    csvfile.flush()
csvfile.close()

#  send email (call function)
print('Emailing: ', len(mail_certs), " new domains to check out today. See attachment.")
r=send_email_from_mailgun()

# log job completion
print("Mailgun status was: ",r.status_code)
job_finish = arrow.utcnow()
print("Ended run at: ", arrow.utcnow().format('YYYY-MM-DD HH:mm:ss'), "and took ",(job_finish-job_start),"to run.")
