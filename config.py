#  WORDS IN ALL CAPS ARE MEANT TO BE REPLACED WITH INFORMATION SPECFIC TO YOUR IMPLEMENTATION/ENVIRONMENT


#  enter list of search terms, use the '%' as a wildcard.
#  each serach term has to be in single quotes, every search term except the last needs a comma after it
list_of_lookup_keys = ['YOUR_SEARCH_TERM_WITH_WILDCARD%',
                       'ANTOHER_SEARCH_TERM_WITHOUT_WILDCARD%']

#  This is the information for the postgres database that you will use to keep a log of results found
my_pghost   = "HOSTNAME_OR_IP_ADDRESS"
my_pgdb   = "DATABASE_NAME"
my_pguser = "USER_NAME"
my_pgpass = "PASSWORD"

#  This is the information needed to use mailgun to send the results
my_mailgun_url = "MAILGUN_URL"
my_mailgun_auth_key = "MAILGUN_APIKEY"


my_from = "Mailgun Sandbox <postmaster@MAILGUN_INSTANCE.mailgun.org>"
my_to = "EMAIL_ADDRESS"
my_subject = "Today's crt.sh results"