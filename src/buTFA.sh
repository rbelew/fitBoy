datestr=`date +"%y-%m-%d-%H:%M"`
cd /home/rik/webapps/django10/fitAlchem/
bakFile="/home/rik/bak/TFA/movegen_"$datestr".json"
ionice -c2 -n6 python3 manage.py dumpdata --exclude auth.permission --exclude contenttypes --indent 1 > $bakFile
# gzip $bakFile
