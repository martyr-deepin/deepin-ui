#!/bin/sh

case "$1" in
    "record" )
        git commit -a
        ;;
    "pull" )
        git pull origin master
        ;;
    "push" )
        git push git@github.com:linuxdeepin/deepin-ui-private.git
        ;;
    "changelog" )
        git log --oneline
        ;;
    "checkout" )
        git checkout -- .
        ;;
    "revert" )
        git revert $2
        ;;
    "add_remote" )
        git remote add $2 git@github.com:$2/deepin-ui.git
        ;;
    "pull_remote" )
        git remote add $2 git@github.com:$2/deepin-ui.git || git fetch $2 && git merge $2/master
        ;;
    "fetch" )
        git fetch $2
        ;;
    "merge" )
        git merge $2/master
        ;;
    "show_remote"  )
        git remote -v
        ;;
    "tag" )
        git tag -a $2
        ;;
    "pushtag" )
        git push git@github.com:$2/deepin-software-center.git --tag
        ;;
    "build"  )
        sudo python setup.py build
        ;;
    "install"  )
        rm -rf `find . -name .#*` | sudo python setup.py install
        ;;
    "module_docs"  )
        epydoc --no-private --html --graph=all -v -o apidocs dtk/ui/$2
        ;;
    "build_html"  )
        sudo python setup.py install && epydoc --graph=all -o apidocs --name Deepin-UI --css epydoc.css --html --parse-only --no-frames --no-private dtk.ui
        ;;
    "build_pdf"  )
        sudo python setup.py install && epydoc --graph=all -o apidocs --name Deepin-UI --css epydoc.css --pdf --parse-only --no-frames --no-private dtk.ui
        ;;
    * ) 
        echo "Help"
        echo "./repos.sh record         => record patch"
        echo "./repos.sh pull           => pull patch"
        echo "./repos.sh push           => push patch"
        echo "./repos.sh changelog      => show changelog"
        echo "./repos.sh checkout       => revert change code"
        echo "./repos.sh revert         => revert patch by id"
        echo "./repos.sh add_remote     => add new remote"
        echo "./repos.sh fetch          => fetch from remote"
        echo "./repos.sh merge          => merge from remote"
        echo "./repos.sh pull_remote    => pull from remote"
        echo "./repos.sh show_remote    => show remote"
        echo "./repos.sh tag            => tag version"
        echo "./repos.sh pushtag        => push tag"
        echo "./repos.sh build          => build deb package"
        echo "./repos.sh install        => install deb package"
        echo "./repos.sh module_docs    => build docs for given module"
        echo "./repos.sh build_html     => build html docs for all modules"
        echo "./repos.sh build_pdf      => build pdf docs for all modules"
        ;;
    esac
