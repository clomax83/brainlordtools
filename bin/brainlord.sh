#!/bin/bash

RESOURCE_PATH="../resources/brainlord"

USER="clomax"
DB_OUT="$RESOURCE_PATH/db/brainlord.db"
DB_IN="/Users/rfontanarosa/git/brainlordapps/resources/brainlord/db/brainlord.db"
SOURCE="$RESOURCE_PATH/roms/Brain Lord (U) [!].smc"
DESTINATION="$RESOURCE_PATH/roms/Brain Lord (I) [!].smc"
TABLE1="$RESOURCE_PATH/tables/Brain Lord (U) [!].tbl"
TABLE2="$RESOURCE_PATH/tables/Brain Lord (I) [!].tbl"

DUMP_MISC_PATH="$RESOURCE_PATH/dump_misc"
TRANSLATION_MISC_PATH="$RESOURCE_PATH/translation_misc"
DUMP_GFX_PATH="$RESOURCE_PATH/dump_gfx"
TANSLATION_GFX_PATH="$RESOURCE_PATH/translation_gfx"
DUMP_TEXT_PATH="$RESOURCE_PATH/dump_text"
TANSLATION_TEXT_PATH="$RESOURCE_PATH/translation_text"

python ../brainlordtools/brainlord.py expand -s "$SOURCE" -d "$DESTINATION"

python ../brainlordtools/brainlord.py dump_misc -s "$SOURCE" -t1 "$TABLE1" -dp "$DUMP_MISC_PATH"
python ../brainlordtools/brainlord.py insert_misc -s "$SOURCE" -d "$DESTINATION" -t1 "$TABLE1" -t2 "$TABLE2" -tp "$TRANSLATION_MISC_PATH"

python ../brainlordtools/brainlord.py dump_gfx -s "$SOURCE" -dp "$DUMP_GFX_PATH"
python ../brainlordtools/brainlord.py insert_gfx -d "$DESTINATION" -tp "$TANSLATION_GFX_PATH"

python ../brainlordtools/brainlord.py dump_text -s "$SOURCE" -t1 "$TABLE1" -dp "$DUMP_TEXT_PATH" -db "$DB_OUT"
python ../brainlordtools/brainlord.py insert_text -s "$SOURCE" -d "$DESTINATION" -t2 "$TABLE2" -tp "$TANSLATION_TEXT_PATH" -db "$DB_IN" -u "$USER"
