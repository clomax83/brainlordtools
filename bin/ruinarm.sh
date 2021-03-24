#!/bin/bash

RESOURCE_PATH="../../brainlordresources/ruinarm"

USER="clomax"
DB="$RESOURCE_PATH/db/ruinarm.sqlite3"
SOURCE="$RESOURCE_PATH/roms/Ruin Arm (J).sfc"
DESTINATION="$RESOURCE_PATH/roms/Ruin Arm (I).sfc"

TABLE1="$RESOURCE_PATH/tables/ruin_arm_utf8.tbl"
TABLE2="$RESOURCE_PATH/tables/ruin_arm_utf8.tbl"

DUMP_TEXT_PATH="$RESOURCE_PATH/dump_text"

TRANSLATION_TEXT_PATH="$RESOURCE_PATH/translation_text"

python3 ../brainlordtools/ruinarm.py dump_text -s "$SOURCE" -t1 "$TABLE1" -dp "$DUMP_TEXT_PATH" -db "$DB"

python3 ../brainlordtools/ruinarm.py insert_text -s "$SOURCE" -d "$DESTINATION" -t2 "$TABLE2" -tp "$TRANSLATION_TEXT_PATH" -db "$DB" -u "$USER"
