#! /bin/bash
rm -f images jquery-ui.css
ln -s ../js/jquery-ui/css/$1/images images
ln -s ../js/jquery-ui/css/$1/jquery-ui-1.8.18.custom.css jquery-ui.css