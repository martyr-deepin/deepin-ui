#!/usr/bin/expect
set timeout 60

spawn /usr/bin/msginit -l $1 -i $2

expect {
    "Please confirm by pressing Return, or enter your email address." {
        send "wangyong@linuxdeepin.com"
    }
}
