from .models import AuditEvent


def client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    return forwarded.split(",")[0].strip() if forwarded else request.META.get("REMOTE_ADDR")


def audit(*, event_type, actor=None, request=None, obj=None, metadata=None):
    return AuditEvent.objects.create(
        actor=actor if getattr(actor, "is_authenticated", False) else None,
        event_type=event_type,
        object_type=obj._meta.label_lower if obj else "",
        object_id=str(obj.pk) if obj else "",
        ip_address=client_ip(request) if request else None,
        metadata=metadata or {},
    )


def assistant_answer(question):
    text = question.casefold()
    if any(term in text for term in ("golpe", "fraude", "senha", "código")):
        return (
            "Nunca compartilhe senha ou código de confirmação. Se alguém criar urgência ou "
            "pedir uma transferência inesperada, pare e procure a instituição pelos canais "
            "oficiais."
        )
    if "pix" in text or "transfer" in text:
        return (
            "O Pix envia valores rapidamente. Antes de confirmar, confira com calma o nome do "
            "destinatário, a chave e o valor. O AMPARO atual é uma demonstração e não envia "
            "dinheiro real."
        )
    if "saldo" in text or "movimenta" in text or "dinheiro" in text:
        return "Seu saldo e cada entrada ou saída demonstrativa aparecem na tela Movimentações."
    if "cartão" in text:
        return (
            "O cartão ainda faz parte da visão futura do AMPARO e não está habilitado nesta "
            "entrega."
        )
    if any(term in text for term in ("letra", "acess", "enxergar", "idos")):
        return "Ative Texto ampliado em Segurança ou Perfil. A preferência fica salva na sua conta."
    return (
        "Posso explicar Pix, saldo, movimentações, segurança contra golpes e acessibilidade em "
        "linguagem simples."
    )
