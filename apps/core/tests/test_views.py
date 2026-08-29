from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User
from apps.core.models import AssistantMessage
from apps.core.services import assistant_answer


class CoreViewTests(TestCase):
    def test_liveness_and_landing(self):
        landing = self.client.get(reverse("landing"))
        self.assertContains(landing, "Seu dinheiro")
        self.assertContains(landing, 'rel="manifest"')
        self.assertContains(landing, "data-font-decrease")
        self.assertContains(landing, "data-font-increase")
        self.assertContains(landing, "data-theme-toggle")
        self.assertContains(landing, "data-contrast-toggle")
        self.assertEqual(self.client.get(reverse("health-live")).json()["status"], "ok")

    def test_service_worker_caches_only_safe_shell(self):
        response = self.client.get(reverse("service-worker"))
        content = response.content.decode()
        self.assertEqual(response["Content-Type"], "application/javascript")
        self.assertEqual(response["Service-Worker-Allowed"], "/")
        self.assertIn("/offline/", content)
        self.assertNotIn("/inicio/", content)

    def test_privacy_policy_is_public_for_oauth_review(self):
        response = self.client.get(reverse("privacy"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Acesso com Google")
        self.assertContains(response, "Dados completos do cartão")

    def test_readiness_checks_database(self):
        response = self.client.get(reverse("health-ready"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["database"], "ok")

    def test_assistant_is_private_and_persists_answer(self):
        user = User.objects.create_user(
            email="ajuda@example.com", password="UmaSenhaForte2026!", full_name="Maria"
        )
        self.client.force_login(user)
        response = self.client.post(reverse("assistant"), {"question": "Como evitar golpe no Pix?"})
        self.assertRedirects(response, reverse("assistant"))
        message = AssistantMessage.objects.get(user=user)
        self.assertIn("Nunca compartilhe", message.answer)

    def test_assistant_answers_cover_supported_topics(self):
        self.assertIn("Pix envia", assistant_answer("Explique o Pix"))
        self.assertIn("Movimentações", assistant_answer("Onde vejo o saldo?"))
        self.assertIn("cartão", assistant_answer("Quero um cartão"))
        self.assertIn("Texto ampliado", assistant_answer("Preciso de acessibilidade"))
        self.assertIn("Posso explicar", assistant_answer("Olá"))
