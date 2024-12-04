DIR=00
if [ -d "00" ]; then
    # Control will enter here if 01 exists.
    DIR=01
    if [ -d "01" ]; then
        DIR=02
        if [ -d "02" ]; then
            DIR=03
            if [ -d "03" ]; then
                DIR=04
                if [ -d "04" ]; then
                    DIR=05
                    if [ -d "05" ]; then
                        DIR=06
                        if [ -d "06" ]; then
                            DIR=07
                            if [ -d "07" ]; then
                                DIR=08
                                if [ -d "08" ]; then
                                    DIR=09
                                fi
                            fi
                        fi
                    fi
                fi
            fi
        fi
    fi
fi
echo "$DIR"
mkdir "$DIR"
mv google/ "$DIR"
mv converted/ "$DIR"
mv converted_withentities/ "$DIR"
mv corpus/ "$DIR"
mv entities/ "$DIR"
mv original/ "$DIR"
mv oslog/ "$DIR"
mv translated/ "$DIR"
mv user\ activity/ "$DIR"
mv userlogs/ "$DIR"
mv language/ "$DIR"
mv persons/ "$DIR"
mv keywords/ "$DIR"
mv listAll.xlsx "$DIR"
mv model_output.xlsx "$DIR"
mv entities_onscreen.xlsx "$DIR"
mkdir user\ activity/
mkdir google/
mkdir converted/
mkdir converted_withentities/
mkdir corpus/
mkdir entities/
mkdir original/
mkdir oslog/
mkdir translated/
mkdir userlogs/
mkdir language/
mkdir persons/
mkdir keywords/
rm /var/www/html/queue_lab/*jpeg*
chmod 777 *
