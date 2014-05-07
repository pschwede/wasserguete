#/bin/bash
set -e

DELIM="\\t"
zip_dir=data/zip
mdb_dir=data/mdb
csv_dir=data/csv

# Download zipped MS Access databases
if [ ! -d $zip_dir ]; then
  mkdir -p $zip_dir
  cd $zip_dir
	wget "http://www.umwelt.sachsen.de/umwelt/wasser/download/ELBE_1998_2013.zip"
	wget "http://www.umwelt.sachsen.de/umwelt/wasser/download/Einzugsgebiet_Elbe_1999_2013.zip"
	wget "http://www.umwelt.sachsen.de/umwelt/wasser/download/Freiberger_Mulde_1999_2013.zip"
	wget "http://www.umwelt.sachsen.de/umwelt/wasser/download/Einzugsgebiet_Freiberger_Mulde_1999_2013.zip"
	wget "http://www.umwelt.sachsen.de/umwelt/wasser/download/Zwickauer_Mulde_1999_2013.zip"
  wget "http://www.umwelt.sachsen.de/umwelt/wasser/download/Einzugsgebiet_Zwickauer_Mulde_1999_2013.zip"
  wget "http://www.umwelt.sachsen.de/umwelt/wasser/download/Vereinigte_Mulde_1999_2013.zip"
	wget "http://www.umwelt.sachsen.de/umwelt/wasser/download/Einzugsgebiet_Vereinigte_Mulde_1999_2013.zip"
	wget "http://www.umwelt.sachsen.de/umwelt/wasser/download/Weisse_Elster_1999_2013.zip"
	wget "http://www.umwelt.sachsen.de/umwelt/wasser/download/Einzugsgebiet_Weisse_Elster_1999_2013.zip"
	wget "http://www.umwelt.sachsen.de/umwelt/wasser/download/Schwarze_Elster_1999_2013.zip"
	wget "http://www.umwelt.sachsen.de/umwelt/wasser/download/Einzugsgebiet_Schwarze_Elster_1999_2013.zip"
	wget "http://www.umwelt.sachsen.de/umwelt/wasser/download/Spree_1999_2013.zip"
	wget "http://www.umwelt.sachsen.de/umwelt/wasser/download/Einzugsgebiet_Spree_1999_2013.zip"
	wget "http://www.umwelt.sachsen.de/umwelt/wasser/download/Lausitzer_Neisse_1999_2013.zip"
	wget "http://www.umwelt.sachsen.de/umwelt/wasser/download/Einzugsgebiet_Lausitzer_Neisse_1999_2013.zip"
  cd -
fi

# Unzip the databases
if [ ! -d $mdb_dir ]; then
	mkdir -p $mdb_dir
	for zip in $(ls $zip_dir/*.zip); do
		unzip -o $zip -d $mdb_dir
	done
fi

# Convert the databases into csv
if [ ! -d $csv_dir ]; then
  for mdb in $(ls $mdb_dir/*.mdb); do
    echo $mdb":"
    mdb-tables $mdb
    for table in $(mdb-tables $mdb); do
      _table=$(echo $table | sed "s/ /_/g")
      mdb_base=$(basename $mdb)
      csv_file="$csv_dir/$mdb_base/$_table".csv
      mkdir -p $csv_dir/$mdb_base
      nice -n 11 mdb-export -d $DELIM $mdb $table > $csv_file &
    done
  done
fi
