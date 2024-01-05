cur_date=""
cd $1
git log --date=format:'%Y-%m-%d' --format="=%ad '%ae'" --name-status | grep -v '^$' | while read l; do
case $l in
    =*)
        cur_date=$l
        ;;
    *)
        echo $cur_date $l
        ;;
esac
done
