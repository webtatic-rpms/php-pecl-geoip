%global php_apiver  %((echo 0; php -i 2>/dev/null | sed -n 's/^PHP API => //p') | tail -1)
%{!?__pecl:     %{expand: %%global __pecl     %{_bindir}/pecl}}
%{!?php_extdir: %{expand: %%global php_extdir %(php-config --extension-dir)}}

%global basepkg   %{?basepkg}%{!?basepkg:php}
%global pecl_name geoip
%global with_zts  0%{?__ztsphp:1}

Name:		%{basepkg}-pecl-geoip
Version:	1.1.1
Release:	1%{?dist}
Summary:	Extension to map IP addresses to geographic places
Group:		Development/Languages
License:	PHP
URL:		http://pecl.php.net/package/%{pecl_name}
Source0:	http://pecl.php.net/get/%{pecl_name}-%{version}.tgz

BuildRoot:	%{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildRequires:	GeoIP-devel
BuildRequires:	%{basepkg}-devel
BuildRequires:	%{basepkg}-pear >= 1:1.4.0
%if 0%{?php_zend_api:1}
Requires:     php(zend-abi) = %{php_zend_api}
Requires:     php(api) = %{php_core_api}
%else
Requires:     php-api = %{php_apiver}
%endif
Requires(post):	%{__pecl}
Requires(postun):	%{__pecl}
Provides:	php-pecl(%{pecl_name}) = %{version}
Provides:       php-pecl-%{pecl_name} = %{version}

%if 0%{?fedora} < 20 && 0%{?rhel} < 7
# Filter private shared
%{?filter_provides_in: %filter_provides_in %{_libdir}/.*\.so$}
%{?filter_setup}
%endif


%description
This PHP extension allows you to find the location of an IP address 
City, State, Country, Longitude, Latitude, and other information as 
all, such as ISP and connection type. It makes use of Maxminds geoip
database

%prep
%setup -c -q
[ -f package2.xml ] || %{__mv} package.xml package2.xml
%{__mv} package2.xml %{pecl_name}-%{version}/%{pecl_name}.xml

# Upstream often forget this
extver=$(sed -n '/#define PHP_GEOIP_VERSION/{s/.* "//;s/".*$//;p}' %{pecl_name}-%{version}/php_geoip.h)
if test "x${extver}" != "x%{version}"; then
   : Error: Upstream version is ${extver}, expecting %{version}.
   exit 1
fi
rm -f %{pecl_name}-%{version}/tests/019.phpt

%if %{with_zts}
cp -r %{pecl_name}-%{version} %{pecl_name}-%{version}-zts
%endif

%build
pushd %{pecl_name}-%{version}
phpize
%configure --with-php-config=%{_bindir}/php-config
%{__make} %{?_smp_mflags}
popd

%if %{with_zts}
pushd %{pecl_name}-%{version}-zts
zts-phpize
%configure --with-php-config=%{_bindir}/zts-php-config
%{__make} %{?_smp_mflags}
popd
%endif

%install
%{__rm} -rf %{buildroot}

pushd %{pecl_name}-%{version}
%{__make} install INSTALL_ROOT=%{buildroot} INSTALL="install -p"
popd

%if %{with_zts}
pushd %{pecl_name}-%{version}-zts
%{__make} install INSTALL_ROOT=%{buildroot} INSTALL="install -p"
popd
%endif

%{__mkdir_p} %{buildroot}%{_sysconfdir}/php.d
%{__cat} > %{buildroot}%{php_inidir}/%{pecl_name}.ini << 'EOF'
; Enable %{pecl_name} extension module
extension=%{pecl_name}.so
EOF

%if %{with_zts}
%{__mkdir_p} %{buildroot}%{php_ztsinidir}
%{__cp} %{buildroot}%{php_inidir}/%{pecl_name}.ini %{buildroot}%{php_ztsinidir}/%{pecl_name}.ini
%endif

%{__mkdir_p} %{buildroot}%{pecl_xmldir}
%{__install} -p -m 644 %{pecl_name}-%{version}/%{pecl_name}.xml %{buildroot}%{pecl_xmldir}/%{name}.xml


#broken on el5 ppc
%check
pushd %{pecl_name}-%{version}
TEST_PHP_EXECUTABLE=$(which php) \
REPORT_EXIT_STATUS=1 \
NO_INTERACTION=1 \
%{_bindir}/php run-tests.php \
    -n -q \
    -d extension_dir=modules \
    -d extension=%{pecl_name}.so
popd

%if %{with_zts}
pushd %{pecl_name}-%{version}-zts
TEST_PHP_EXECUTABLE=$(which zts-php) \
REPORT_EXIT_STATUS=1 \
NO_INTERACTION=1 \
%{_bindir}/zts-php run-tests.php \
    -n -q \
    -d extension_dir=modules \
    -d extension=%{pecl_name}.so
popd
%endif

%clean
%{__rm} -rf %{buildroot}


%if 0%{?pecl_install:1}
%post
%{pecl_install} %{pecl_xmldir}/%{name}.xml >/dev/null || :
%endif

%if 0%{?pecl_uninstall:1}
%postun
if [ $1 -eq 0 ]  ; then
%{pecl_uninstall} %{pecl_name} >/dev/null || :
fi
%endif

%files
%defattr(-,root,root,-)
%doc %{pecl_name}-%{version}/{README,ChangeLog}
%config(noreplace) %{php_inidir}/%{pecl_name}.ini
%{php_extdir}/%{pecl_name}.so
%{pecl_xmldir}/%{name}.xml

%if %{with_zts}
%config(noreplace) %{php_ztsinidir}/%{pecl_name}.ini
%{php_ztsextdir}/%{pecl_name}.so
%endif

%changelog
* Sun Jun 11 2017 Andy Thompson <andy@webtatic.com> - 1.1.1-1
- Update to geoip 1.1.1
- Remove tests patch fixed upstream
- Remove 019 incomplete test

* Sat Sep 13 2014 Andy Thompson <andy@webtatic.com> - 1.0.8-2
- Remove .so filter provider on EL7
- Tie zts compilation to macro

* Sun Jul 27 2014 Andy Thompson <andy@webtatic.com> - 1.0.8-1
- Fork from php55w-pecl-geoip-1.0.8-1
