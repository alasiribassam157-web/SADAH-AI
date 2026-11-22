"""Builder facts: what is stated inside a request reaches the site; nothing is invented; digits never turn into data.
Offline, no PyTorch.

Run:  python -m tests.builder_facts_test
"""
import unittest

from builder import checks, facts
from builder.build import build
from builder.understand import understand

CAR_WASH = "ابغى موقع لمغسلة سيارات باسم لمعان وخدماتنا غسيل داخلي وتلميع وتنظيف محرك وجوالي 0501234567 في جدة"


class Extraction(unittest.TestCase):
    def test_every_kind_of_fact_is_read_as_typed(self):
        f = facts.extract("باسم س ايميلنا info@x.com جوالي +966501234567 ونعمل من 9 صباحا الى 11 مساء في الرياض "
                          "بتاريخ 15/12/2026 الساعة 8 مساء في قاعة الماسة").facts
        self.assertEqual(f, {"email": "info@x.com", "phone": "+966501234567", "hours": "من 9 صباحا الى 11 مساء",
                             "place": "قاعة الماسة", "time": "8 مساء", "date": "15/12/2026", "city": "الرياض"})

    def test_a_weekday_is_a_date_and_a_city_inside_a_place_is_not_a_second_fact(self):
        self.assertEqual(facts.extract("حفل يوم الخميس").facts, {"date": "الخميس"})
        self.assertNotIn("city", facts.extract("في فندق الريتز الرياض").facts)

    def test_nothing_is_invented_from_a_bare_request(self):
        got = facts.extract("ابغى موقع لمقهى باسم ركن القهوة")
        self.assertEqual((got.facts, got.services), ({}, []))

    def test_services_split_at_glued_waw_and_commas_and_stop_at_the_next_fact(self):
        self.assertEqual(facts.extract("نقدم غسيل سيارات وتلميع، صيانة ولونه احمر").services, ["غسيل سيارات", "تلميع", "صيانة"])

    def test_section_words_after_services_are_sections_not_services(self):
        self.assertEqual(understand("موقع لمكتب باسم رحلاتنا وفيه خدماتنا وتواصل").spec.services, [])
        self.assertEqual(understand("موقع لمركز باسم مهارة وفيه خدماتنا واسعار").spec.services, [])

    def test_phone_digits_are_never_a_shop_item_or_a_dashboard_value_or_a_name(self):
        shop = understand("متجر باسم عبق وفيه بخور 50 ودهن عود 200 وجوالي 0501112222").spec
        self.assertEqual([n for n, _ in shop.items], ["بخور", "دهن عود"])
        dash = understand("لوحة بيانات باسم الطلبات فيها اليوم 40 امس 35 جوالي 0501112222").spec
        self.assertEqual([v for _, v in dash.data], [40.0, 35.0])
        self.assertEqual(understand("موقع لمطعم باسم النخبة جوالي 0501112222").spec.name, "النخبة")


class Rendering(unittest.TestCase):
    def test_the_site_carries_the_stated_facts_and_the_checks_still_pass(self):
        r = build(CAR_WASH)
        html = r.files["index.html"]
        for text in ("غسيل داخلي", "تلميع", "تنظيف محرك", "0501234567", "جدة"):
            self.assertIn(text, html)
        self.assertNotIn("خدمتنا الأولى", html)   # the stated services replace the defaults
        self.assertEqual(checks.check_site(r.files), [])

    def test_missing_facts_keep_the_editable_placeholder_and_hours_appear_only_when_stated(self):
        html = build("موقع لمقهى باسم ركن القهوة").files["index.html"]
        self.assertIn("الهاتف: (عدّل هذا النص)", html)
        self.assertNotIn("ساعات العمل", html)
        self.assertIn("ساعات العمل: من 9 صباحا الى 5 مساء", build("موقع لمقهى باسم قهوتي ونعمل من 9 صباحا الى 5 مساء").files["index.html"])

    def test_event_details_use_date_time_and_place(self):
        html = build("دعوة لحفل زفاف باسم زفاف نورة وفهد يوم الخميس الساعة 8 مساء في قاعة الماسة").files["index.html"]
        for text in ("التاريخ: الخميس", "الوقت: 8 مساء", "المكان: قاعة الماسة"):
            self.assertIn(text, html)

    def test_a_shop_without_prices_uses_the_stated_products(self):
        r = build("متجر باسم الخير ونبيع تمر وقهوة وهيل")
        self.assertEqual([n for n, _ in r.spec.items], ["تمر", "قهوة", "هيل"])

    def test_phone_is_wrapped_so_it_reads_left_to_right_inside_arabic(self):
        self.assertIn('<bdi dir="ltr">+966501234567</bdi>', build("موقع لصالون باسم فخامة وواتساب +966501234567").files["index.html"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
