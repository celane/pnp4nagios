Name:           pnp4nagios
Version:        0.6.27
Release:        2%{?dist}
Summary:        Nagios performance data analysis tool

Group:          Applications/System
License:        GPLv2
URL:            https://github.com/celane/pnp4nagios
Source0:        %{name}-%{version}.tar.gz
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root

#BuildRequires:  git
BuildRequires:  autoconf, automake, libtool
BuildRequires:  rrdtool-perl
BuildRequires:  perl(Time::HiRes)
Requires:       nagios
Requires:       rrdtool-perl
Requires:       php >= 5.6
Requires:       php-gd
Requires:       php-xml
Requires:       php-mbstring
Requires:       systemd

%description
PNP is an addon to nagios which analyzes performance data provided by plugins
and stores them automatically into RRD-databases.

%prep
%setup -q -n %{name}-%{version}
autoreconf

cp contrib/fedora/pnp4nagios-README.fedora README.fedora
sed -i -e 's/^INSTALL_OPTS="-o $nagios_user -g $nagios_grp"/INSTALL_OPTS=""/' \
    configure
sed -i -e '/^\t$(MAKE) strip-post-install$/d' src/Makefile.in


%build
%configure --bindir=%{_sbindir} \
           --libexecdir=%{_libexecdir}/%{name} \
           --sysconfdir=%{_sysconfdir}/%{name} \
           --localstatedir=%{_localstatedir}/log/%{name} \
           --datadir=%{_datadir}/nagios/html/%{name} \
           --datarootdir=%{_datadir}/nagios/html/%{name} \
           --with-perfdata-dir=%{_localstatedir}/lib/%{name} \
           --with-perfdata-spool-dir=%{_localstatedir}/spool/%{name}
make %{?_smp_mflags} all


%install
if [ "$RPM_BUILD_ROOT" != "/" ]; then
    rm -rf $RPM_BUILD_ROOT
fi
make install DESTDIR=$RPM_BUILD_ROOT 
make install-config DESTDIR=$RPM_BUILD_ROOT 
# NO...do NOT remove -sample from filename suffix
#for i in $RPM_BUILD_ROOT/%{_sysconfdir}/pnp4nagios/*-sample \
#         $RPM_BUILD_ROOT/%{_sysconfdir}/pnp4nagios/*/*-sample
#do
#  mv ${i} ${i%%-sample}
#done
rm -f $RPM_BUILD_ROOT%{_sysconfdir}/%{name}/config.php.*
rm -f $RPM_BUILD_ROOT%{_sysconfdir}/%{name}/config_local.php

mkdir -p $RPM_BUILD_ROOT%{_localstatedir}/lib/%{name}
mkdir -p $RPM_BUILD_ROOT%{_localstatedir}/spool/%{name}
mkdir -p $RPM_BUILD_ROOT%{_localstatedir}/log/%{name}
#
install -Dp -m 0644 contrib/fedora/pnp4nagios.logrotate.conf \
        $RPM_BUILD_ROOT%{_sysconfdir}/logrotate.d/pnp4nagios
#
mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}/logwatch/scripts/services
mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}/logwatch/conf/services
mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}/logwatch/conf/logfiles
install -m 0666 contrib/fedora/logwatch/scripts/services/pnp4nagios \
        $RPM_BUILD_ROOT%{_sysconfdir}/logwatch/scripts/services/
install -m 0644 contrib/fedora/logwatch/conf/services/pnp4nagios.conf \
        $RPM_BUILD_ROOT%{_sysconfdir}/logwatch/conf/services/
install -m 0644 contrib/fedora/logwatch/conf/logfiles/pnp4nagios.conf \
        $RPM_BUILD_ROOT%{_sysconfdir}/logwatch/conf/logfiles/
#
mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}/systemd/system/httpd.service.d
install -m 0644 contrib/fedora/pnp4nagios.httpd.plugin.conf \
  $RPM_BUILD_ROOT%{_sysconfdir}/systemd/system/httpd.service.d/pnp4nagios.conf
mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}/httpd/conf.d
sed 's|/usr/local/nagios/etc/htpasswd.users|/etc/nagios/passwd|' \
   sample-config/httpd.conf \
   > $RPM_BUILD_ROOT%{_sysconfdir}/httpd/conf.d/%{name}.conf
install -Dp -m 0644 contrib/fedora/npcd.sysconfig \
        $RPM_BUILD_ROOT%{_sysconfdir}/sysconfig/npcd
install -Dp -m 0644 contrib/fedora/npcd.service \
        $RPM_BUILD_ROOT%{_unitdir}/npcd.service
mkdir -p $RPM_BUILD_ROOT%{_libdir}/nagios/brokers
mv $RPM_BUILD_ROOT%{_libdir}/npcdmod.o \
   $RPM_BUILD_ROOT%{_libdir}/nagios/brokers/npcdmod.o
mv $RPM_BUILD_ROOT%{_prefix}/man $RPM_BUILD_ROOT%{_datadir}/

# Move kohana to pnp4nagios, there is another kohana in fedore/EPEL,
# which can be installed.
mv $RPM_BUILD_ROOT%{_libdir}/kohana \
  $RPM_BUILD_ROOT%{_datadir}/nagios/html/%{name}/kohana
sed -i 's|%{_libdir}/kohana|%{_datadir}/nagios/html/%{name}/kohana|' \
  $RPM_BUILD_ROOT%{_datadir}/nagios/html/%{name}/index.php


%package logrotate
Summary:        config for rotating pnp4nagios logs
Requires:       logrotate
Group:          Applications/System

%description logrotate
config file used by logrotate, set up for pnp4nagios logs


%package logwatch
Summary:        config and scripts for checking pnp4nagios log files
Requires:       logwatch
Group:          Applications/System

%description logwatch
config files and log scanning script for checking pnp4nagios log
files for errors, and flagging them for attention. 


%clean
#if [ "$RPM_BUILD_ROOT" != "/" ]; then
#   rm -rf $RPM_BUILD_ROOT
#fi



%files
%defattr(644,root,root,755)
%doc AUTHORS ChangeLog COPYING
%doc INSTALL README.md README.fedora
%doc THANKS contrib/
%dir %{_sysconfdir}/pnp4nagios
%config(noreplace) %{_sysconfdir}/pnp4nagios/*
%config(noreplace) %{_sysconfdir}/httpd/conf.d/%{name}.conf
%config(noreplace) %{_sysconfdir}/sysconfig/npcd
%config(noreplace) %{_sysconfdir}/systemd/system/httpd.service.d/*
%attr(755,root,root) %{_sbindir}/npcd
%{_unitdir}/npcd.service
%{_libdir}/nagios/brokers/npcdmod.o
%dir %{_libexecdir}/%{name}
%attr(755,root,root) %{_libexecdir}/%{name}/*
%attr(755,nagios,nagios) %{_localstatedir}/lib/%{name}
%attr(755,nagios,nagios) %{_localstatedir}/log/%{name}
%attr(755,nagios,nagios) %{_localstatedir}/spool/%{name}
%{_datadir}/nagios/html/%{name}
# Remove install check script
# as it is not required if all dependencies are met.
%exclude %{_datadir}/nagios/html/%{name}/install.php
%{_mandir}/man8/*

%files logrotate
%config(noreplace) %{_sysconfdir}/logrotate.d/%{name}

%files logwatch
%defattr(644,root,root)
%config(noreplace)%{_sysconfdir}/logwatch/scripts/services/%{name}
%config(noreplace) %{_sysconfdir}/logwatch/conf/services/%{name}.conf
%config(noreplace) %{_sysconfdir}/logwatch/conf/logfiles/%{name}.conf


%post
systemctl daemon-reload
systemctl try-restart npcd

%changelog
* Fri Aug 18 2023 Chuck Lane <lane@dhooz.org> - 0.6.27-1
- many pnp8.2 deprecation fixes, get XDG_CACHE_HOME in systemd setup
  
* Tue Dec 20 2022 Chuck Lane <lane@dchooz.org> - 0.6.26-14
- minor config cleanups, add logwatch and logrotate subpackages

* Sun Sep 11 2022 Chuck Lane <lane@dchooz.org> - 0.6.26-3
- upgrade to php8

* Mon Jun 08 2015 Ján ONDREJ (SAL) <ondrejj(at)salstar.sk> - 0.6.25-1
- Update to upstream.

* Sun Aug 17 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.6.22-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_22_Mass_Rebuild

* Fri Jul 04 2014 Ján ONDREJ (SAL) <ondrejj(at)salstar.sk> - 0.6.22-2
- Fix two URL Cross-Site Scripting Vulnerabilities (bz#1115983)

* Thu Jul 03 2014 Ján ONDREJ (SAL) <ondrejj(at)salstar.sk> - 0.6.22-1
- Update to upstream (fixes XSS flaw in an error page - bz#1115770)

* Sat Jun 07 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.6.21-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_Mass_Rebuild

* Sun Aug 04 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.6.21-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_20_Mass_Rebuild

* Wed Jul 17 2013 Petr Pisar <ppisar@redhat.com> - 0.6.21-3
- Perl 5.18 rebuild

* Wed Jul 03 2013 Ján ONDREJ (SAL) <ondrejj(at)salstar.sk> - 0.6.21-2
- Broken configuration for httpd 2.4 fixed (bz#871465)
- fixed dates in changelog items

* Tue Jun 04 2013 Ján ONDREJ (SAL) <ondrejj(at)salstar.sk> - 0.6.21-1
- update to upstream

* Sat Mar 23 2013 Ján ONDREJ (SAL) <ondrejj(at)salstar.sk> - 0.6.20-2
- added autoreconf to prep section (bz#926359)

* Sun Mar 03 2013 Ján ONDREJ (SAL) <ondrejj(at)salstar.sk> - 0.6.20-1
- update to upstream

* Sun Feb 17 2013 Ján ONDREJ (SAL) <ondrejj(at)salstar.sk> - 0.6.19-2
- updated hostextinfo URL for pnp4nagios 0.6
- spec file cleanup

* Sat Feb 16 2013 Ján ONDREJ (SAL) <ondrejj(at)salstar.sk> - 0.6.19-1
- update to upstream

* Mon Sep 03 2012 Ján ONDREJ (SAL) <ondrejj(at)salstar.sk> - 0.6.16-4
- CVE-2012-3457 - process_perfdata.cfg world readable

* Thu Apr 05 2012 Ján ONDREJ (SAL) <ondrejj(at)salstar.sk> - 0.6.16-2
- Removed double slashes fro directories (BZ#810212).

* Thu Nov 24 2011 Ján ONDREJ (SAL) <ondrejj(at)salstar.sk> - 0.6.16-1
- update to upstream

* Mon Nov 21 2011 Ján ONDREJ (SAL) <ondrejj(at)salstar.sk> - 0.6.15-4
- add back kohana, it's a different version
- added BR: perl(Time::HiRes)

* Mon Nov 21 2011 Ján ONDREJ (SAL) <ondrejj(at)salstar.sk> - 0.6.15-2
- exclude kohana sources and require php-Kohana package

* Wed Nov 16 2011 Ján ONDREJ (SAL) <ondrejj(at)salstar.sk> - 0.6.15-1
- update to upstream
- remove /usr/share/nagios/html/pnp4nagios/install.php
- added /etc/httpd/conf.d/pnp4nagios.conf
- removed -sample suffix from rest of sample files

* Tue Oct 11 2011 Ján ONDREJ (SAL) <ondrejj(at)salstar.sk> - 0.6.1-3
- Updated renaming of "-sample" config files.

* Wed Sep 14 2011 Ján ONDREJ (SAL) <ondrejj(at)salstar.sk> - 0.6.1-1
- Update to 0.6.1.

* Tue Sep 13 2011 Ján ONDREJ (SAL) <ondrejj(at)salstar.sk> - 0.4.14-7
- added perl-Time-HiRes to build requires

* Tue Sep 13 2011 Ján ONDREJ (SAL) <ondrejj(at)salstar.sk> - 0.4.14-6
- rebuilt for EPEL-6

* Wed Feb 09 2011 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.4.14-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_15_Mass_Rebuild

* Mon Sep 27 2010 Xavier Bachelot <xavier@bachelot.org> 0.4.14-4
- Bump release for rebuild.

* Sun Jul 18 2010 Xavier Bachelot <xavier@bachelot.org> 0.4.14-3
- Add patch to fix PHP deprecated warnings with PHP 5.3.
  (Patch from Jan Ondrej - RHBZ#572851)

* Thu Aug 27 2009 Xavier Bachelot <xavier@bachelot.org> 0.4.14-2
- Ship contrib directory as doc.

* Thu Aug 27 2009 Xavier Bachelot <xavier@bachelot.org> 0.4.14-1
- Update to 0.4.14 (RHBZ#518069).
- Fix typo in README.fedora (RHBZ#490664).
- Move npcdmod.o to a better place.
- BR: rrdtool-perl

* Sun Jul 26 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.4.12-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_12_Mass_Rebuild

* Thu Feb 26 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.4.12-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_11_Mass_Rebuild

* Thu Dec  4 2008 Michael Schwendt <mschwendt@fedoraproject.org> 0.4.12-2
- Include /usr/libexec/pnp4nagios directory.

* Tue Oct 21 2008 Robert M. Albrecht <romal@gmx.de> 0.4.12-1
- Upstream released 0.4.12

* Tue Sep 02 2008 Xavier Bachelot <xavier@bachelot.org> 0.4.10-3
- Fix logrotate conf (RHBZ#460861).

* Fri Jul 18 2008 Xavier Bachelot <xavier@bachelot.org> 0.4.10-2
- Fix typo in logrotate conf.

* Wed Jul 09 2008 Xavier Bachelot <xavier@bachelot.org> 0.4.10-1
- Update to 0.4.10.

* Tue May 27 2008 Xavier Bachelot <xavier@bachelot.org> 0.4.9-3
- Fix npcd init script to use /etc/pnp4nagios.

* Tue May 27 2008 Xavier Bachelot <xavier@bachelot.org> 0.4.9-2
- Install npcd unstripped to let rpm do it.

* Sat May 24 2008 Xavier Bachelot <xavier@bachelot.org> 0.4.9-1
- Update to 0.4.9.
- Rename to pnp4nagios to match other distros packages.

* Mon Apr 14 2008 Xavier Bachelot <xavier@bachelot.org> 0.4.7-5
- Log to file by default.
- Kill pnpsender man page.

* Mon Apr 07 2008 Xavier Bachelot <xavier@bachelot.org> 0.4.7-4
- Install inside of nagios html dir.

* Mon Apr 07 2008 Xavier Bachelot <xavier@bachelot.org> 0.4.7-3
- Provide properly named config files.
- Add missing Requires:.
- Add a logrotate conf file.

* Fri Apr 04 2008 Xavier Bachelot <xavier@bachelot.org> 0.4.7-2
- Add an initscript for npcd.

* Wed Mar 19 2008 Xavier Bachelot <xavier@bachelot.org> 0.4.7-1
- Initial build.
