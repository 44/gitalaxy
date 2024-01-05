cur_date=""
git log --date=format:'%Y-%m-%d' --format='%ad' --name-only | grep -v '^$' | while read l; do
case $l in
    20*)
        cur_date=$l
        ;;
    *)
        echo $cur_date $l
        ;;
esac
done
