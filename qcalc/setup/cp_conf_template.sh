# This linux shell script can be RUN FROM any folder
rm -f ~/qcalc_dock/.local/nginx/conf/default.conf
cp ~/qcalc_dock/.local/nginx/templates/default.conf.template.off \
   ~/qcalc_dock/.local/nginx/templates/default.conf.template
