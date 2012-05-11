#!/bin/sh

echo "Copy theme files..."
for theme_name in 000000 FF0000 FF6C00 FFC600 FCFF00 C0FF00 00FF60 00FDFF 00A8FF 0006FF 8400FF BA00FF FF00B4 333333
do 
    echo "Copy theme: " $2/$theme_name
    cp -r $1 $2/$theme_name
done
echo "Copy theme files done."

echo "Convert color..."
for theme_name in 000000 FF0000 FF6C00 FFC600 FCFF00 C0FF00 00FF60 00FDFF 00A8FF 0006FF 8400FF BA00FF FF00B4 333333
do 
    echo "Convert color: " $2/$theme_name
    for img in `find $2/$theme_name -type f \\( -name *.png -o -name *.jpg -o -name *.ico -o -name *.jpeg \\)`
    do 
        convert $img -fill "#"$theme_name -colorize 50% $img
    done
done
echo "Convert color done."
