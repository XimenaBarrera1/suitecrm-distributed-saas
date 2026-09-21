FROM php:8.2-apache

ARG SUITECRM_VERSION=7.15.1

RUN apt-get update && apt-get install -y \
    unzip \
    curl \
    libzip-dev \
    libpng-dev \
    libjpeg-dev \
    libfreetype6-dev \
    libicu-dev \
    libxml2-dev \
    libonig-dev \
    libldap2-dev \
    libcurl4-openssl-dev \
    libssl-dev \
    zlib1g-dev \
    mariadb-client \
    && docker-php-ext-configure gd --with-freetype --with-jpeg \
    && docker-php-ext-configure ldap \
    && docker-php-ext-install \
        mysqli \
        pdo \
        pdo_mysql \
        zip \
        gd \
        intl \
        soap \
        mbstring \
        opcache \
        ldap \
        curl \
    && pecl install redis \
    && docker-php-ext-enable redis \
    && a2enmod rewrite headers expires \
    && rm -rf /var/lib/apt/lists/*

RUN curl -L -o /tmp/suitecrm.zip \
    "https://github.com/SuiteCRM/SuiteCRM/releases/download/v${SUITECRM_VERSION}/SuiteCRM-${SUITECRM_VERSION}.zip" \
    && mkdir -p /usr/src/suitecrm \
    && unzip /tmp/suitecrm.zip -d /tmp/suitecrm \
    && cp -a /tmp/suitecrm/SuiteCRM-${SUITECRM_VERSION}/. /usr/src/suitecrm/ \
    && rm -rf /tmp/suitecrm /tmp/suitecrm.zip

COPY apache/suitecrm.conf /etc/apache2/sites-available/000-default.conf
COPY php/custom.ini /usr/local/etc/php/conf.d/custom.ini
COPY entrypoint.sh /usr/local/bin/suitecrm-entrypoint.sh

RUN chmod +x /usr/local/bin/suitecrm-entrypoint.sh \
    && chown -R www-data:www-data /usr/src/suitecrm /var/www/html

ENTRYPOINT ["suitecrm-entrypoint.sh"]