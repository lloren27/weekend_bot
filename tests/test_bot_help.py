import unittest

from bot import build_help_text


class BotHelpTest(unittest.TestCase):

    def test_help_text_includes_all_commands(self):
        text = build_help_text()

        for command in (
            "/planes",
            "/conciertos",
            "/exposiciones",
            "/ferias",
            "/fiestas_regionales",
            "/deporte_profesional",
            "/running",
            "/ciclismo",
            "/help",
            "/id",
        ):
            self.assertIn(
                command,
                text,
            )


if __name__ == "__main__":
    unittest.main()
