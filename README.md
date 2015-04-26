# README #

This README would normally document whatever steps are necessary to get your application up and running.

### What is this repository for? ###

* Quick summary
* Version
* [Learn Markdown](https://bitbucket.org/tutorials/markdowndemo)

### How do I get set up? ###

* Summary of set up
####��� ��������� ��������� ��� ����� �����:

1. ���������� VirtualBox ( https://www.virtualbox.org/wiki/Downloads ) 

2. ���������� Vagrant ( http://www.vagrantup.com/downloads.html ) 

3. ���������� git ( http://git-scm.com/ )

4. � ��������� (� Windows ����� ��������������� Git Bash )
   ��������� � ����� � ���������. � �������� �����������.
   ��������:

        cd /home/user/Projects
        git clone git@bitbucket.org:Gvammer/heliard.git heliard

5. ��������� � ����� � �������� � ��������� ����������� ������ (� ������ ��� ������ ����� ��������� �����.

        vagrant up

6. ��� ������ ����� ������� ��� heliard.dev �������� ������ ������� 192.168.33.13.
    ����� ����� ������� ��� � ����� hosts.
    *Linux*
    �������� ������� 

        192.168.33.13     heliard.dev

    � ���� /etc/hosts

     *Windows*
     �������� ��������� ������ � ������ �������������� (������ ������� �� ������ - ��������� �� ����� ��������������).
     ���������

        notepad %WINDIR%\System32\drivers\etc\hosts

    �������� �������

        192.168.33.13     heliard.dev

7. **������ ������ ��������������� ��� ���� ������**
 ������� ���������� ���������������� ����.
 �������� � ����������� ���� ����� ���� dump.sql � ������� �������� 
 � ��������� ��� � ���������� �������. �����: 

        vagrant ssh
        cd /vagrant
        mysql -u root -p < dump.sql

    ����������� ������ ������ - ������� root 
    (���� ����� �� ����� ������ ������� Ctrl+C � ������� 

        sudo service mysql restart

    � ��������� �������.
        
        rm -f dump.sql
        python manage.py schemamigration --initial
        exit

8. ����� ����������� ������ ���������� ��������� � bash ���������

        vagrant provision

9. �������� � �������� �������� [heliard.dev](http://heliard.dev)

* Configuration
* Dependencies
* Database configuration
* How to run tests
* Deployment instructions

### Contribution guidelines ###

* Writing tests
* Code review
* Other guidelines

### Who do I talk to? ###

* Repo owner or admin
* Other community or team contact