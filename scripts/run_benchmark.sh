for i in $(seq 100)
do
    echo -n "$i: "
    ( time python tracerappcode.py $i ) 2>&1 | grep real
done
