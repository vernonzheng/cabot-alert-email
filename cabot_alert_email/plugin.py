# -*- coding:UTF-8 -*-
from os import environ as env

from django.conf import settings
from django.core.mail import send_mail, EmailMultiAlternatives
from django.core.urlresolvers import reverse
from django.template import Context, Template, loader

from cabot.plugins.models import AlertPlugin

import requests
import logging
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

email_template = """<html><head><style type='text/css'>table{border-collapse:collapse;}th{empty-cells:show;border:1px solid black ;background-color:green;color:white;font-size:13px;}</style>
</head>Service {{ service.name }} {{ scheme }}://{{ host }}{% url 'service' pk=service.id %} {% if service.overall_status != service.PASSING_STATUS %}alerting with status: {{ service.overall_status }}{% else %}is back to normal{% endif %}.
<br/>
{% if service.overall_status != service.PASSING_STATUS %}
<p>
<strong>校验结果列表</strong>
<br/>
<table border='1px'>
<tr><th>检查结果</th><th>检查名称</th><th>类型</th><th>重要性</th><th>频率</th><th>防抖数量</th><th>实际值</th></tr>
{% if service.overall_status != service.PASSING_STATUS %}
{% for check in service.all_failing_checks %}
<tr><td><font color="red">FAILING</font></td><td>{{ check.name }}</td><td>{{ check.check_category }}</td><td>{{ check.get_importance_display }}</td><td>{{ check.frequency }}分钟</td><td>{{ check.debounce }}</td><td>{% autoescape off %}{{ check.error|default:"" }}{% endautoescape %}</td></tr>
{% endfor %}
{% if service.all_passing_checks %}
{% for check in service.all_passing_checks %}
<tr><td><font color="green">PASSING</font></td><td>{{ check.name }}</td><td>{{ check.check_category }}</td><td>{{ check.get_importance_display }}</td><td>{{ check.frequency }}分钟</td><td>{{ check.debounce }}</td><td>{% autoescape off %}{{ check.error|default:"" }}{% endautoescape %}</td></tr>
{% endfor %}
{% endif %}
{% endif %}
{% endif %}
</table>
</html>
"""

class EmailAlertPlugin(AlertPlugin):
    name = "Email"
    slug = "cabot_alert_email"
    author = "Jonathan Balls"
    version = "0.0.1"
    font_icon = "fa fa-envelope"

    plugin_variables = [
        'ADMIN_EMAIL',
        'CABOT_FROM_EMAIL'
    ]

    def send_alert(self, service, users, duty_officers):
        emails = [u.email for u in users if u.email]
        if not emails:
            return
        fail_count = service.all_failing_checks().count()
        c = Context({
            'service': service,
            'host': settings.WWW_HTTP_HOST,
            'scheme': settings.WWW_SCHEME
        })

        if service.overall_status != service.PASSING_STATUS:
            if service.overall_status == service.CRITICAL_STATUS:
                emails += [u.email for u in users if u.email]
            subject = '[%s]状态变为:%s,失败数:%s' % (
                service.name, service.overall_status, fail_count)
        else:
            subject = '[%s]状态变为:正常' % (service.name,)
        t = Template(email_template)
        html_content = t.render(c)
        msg = EmailMultiAlternatives(subject, html_content, 'Cabot <%s>' % env.get('CABOT_FROM_EMAIL'), emails)
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        """
        send_mail(
            subject=subject,
            message=t.render(c),
            from_email='Cabot <%s>' % env.get('CABOT_FROM_EMAIL'),
            recipient_list=emails,
        )
        """

