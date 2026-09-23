from django.apps import AppConfig
import unicodedata
import re


def remove_accents(input_str):
    if not input_str:
        return ''
    nfkd = unicodedata.normalize('NFKD', str(input_str))
    res = ''.join([c for c in nfkd if not unicodedata.combining(c)]).lower()
    return res.replace('đ', 'd').replace('Đ', 'd')


def sqlite_custom_like(pattern, string, escape='\\'):
    if string is None or pattern is None:
        return False
    p = str(pattern)
    s = str(string)

    # Fast path for %term% substring check (most common in Django icontains)
    if p.startswith('%') and p.endswith('%') and '%' not in p[1:-1] and '_' not in p:
        target = p[1:-1].lower()
        s_lower = s.lower()
        if target in s_lower or remove_accents(target) in remove_accents(s_lower):
            return True
        return False

    # Generic pattern matching
    esc = escape if escape else '\\'
    try:
        p_lower = p.lower()
        s_lower = s.lower()
        tokens = []
        i = 0
        while i < len(p_lower):
            if p_lower[i] == esc and i + 1 < len(p_lower):
                tokens.append(re.escape(p_lower[i + 1]))
                i += 2
            elif p_lower[i] == '%':
                tokens.append('.*')
                i += 1
            elif p_lower[i] == '_':
                tokens.append('.')
                i += 1
            else:
                tokens.append(re.escape(p_lower[i]))
                i += 1
        regex_str = '^' + ''.join(tokens) + '$'
        if re.search(regex_str, s_lower, re.DOTALL | re.IGNORECASE):
            return True

        p_noacc = remove_accents(p)
        s_noacc = remove_accents(s)
        tokens_noacc = []
        i = 0
        while i < len(p_noacc):
            if p_noacc[i] == esc and i + 1 < len(p_noacc):
                tokens_noacc.append(re.escape(p_noacc[i + 1]))
                i += 2
            elif p_noacc[i] == '%':
                tokens_noacc.append('.*')
                i += 1
            elif p_noacc[i] == '_':
                tokens_noacc.append('.')
                i += 1
            else:
                tokens_noacc.append(re.escape(p_noacc[i]))
                i += 1
        regex_noacc = '^' + ''.join(tokens_noacc) + '$'
        if re.search(regex_noacc, s_noacc, re.DOTALL):
            return True
    except Exception:
        pass
    return False


def setup_sqlite_connection(sender, connection, **kwargs):
    if connection.vendor == 'sqlite':
        connection.connection.create_function('LIKE', 2, lambda p, s: sqlite_custom_like(p, s))
        connection.connection.create_function('LIKE', 3, lambda p, s, e: sqlite_custom_like(p, s, e))


class MainConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'main'
    verbose_name = 'Quản lý hệ thống'

    def ready(self):
        from django.db.backends.signals import connection_created
        connection_created.connect(setup_sqlite_connection)
        import main.signals
