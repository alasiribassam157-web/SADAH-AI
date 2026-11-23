"""The shop's cart: the page and script agree, nothing is injected, nothing is paid, and only a shop gets one."""
import re
import unittest
from dataclasses import replace

from builder import api, checks, edit
from builder.build import build, render as build_from

SHOP = "متجر ملابس باسم أناقة فيه عبايات 250 وفساتين 320 وحجابات 45 وشنطة"


class Cart(unittest.TestCase):
    def setUp(self):
        self.r = build(SHOP)
        self.html, self.js = self.r.files["index.html"], self.r.files["app.js"]

    def test_the_shop_builds_with_a_cart_and_passes_every_check(self):
        self.assertTrue(self.r.ok, self.r.problems)
        self.assertEqual(checks.check_site(self.r.files), [])
        self.assertIn('<script src="app.js"></script>', self.html)

    def test_every_element_the_script_looks_for_is_in_the_page(self):
        for ident in re.findall(r'getElementById\("([^"]+)"\)', self.js):
            self.assertIn(f'id="{ident}"', self.html, ident)

    def test_each_product_has_an_add_button_and_priced_ones_carry_their_price(self):
        for name, price in self.r.spec.items:
            self.assertIn(f'data-add="{name}"', self.html)
        self.assertIn('data-name="عبايات" data-price="250" data-unit="ريال"', self.html)
        self.assertEqual(len(re.findall(r"data-add=", self.html)), len(self.r.spec.items))

    def test_the_item_without_a_price_still_goes_in_the_cart_and_is_not_priced(self):
        html = build_from(replace(self.r.spec, items=[("شنطة", "")])).files["index.html"]
        card = re.search(r'<div class="card" data-name="شنطة"[^>]*>', html).group(0)
        self.assertNotIn("data-price", card)
        self.assertIn("سعرها عند التواصل", self.js)

    def test_the_script_never_builds_html_from_text_or_reaches_out(self):
        for bad in ("innerHTML", "fetch(", "XMLHttpRequest", "eval(", "http", "window.open", "location"):
            self.assertNotIn(bad, self.js)

    def test_names_cannot_break_out_of_the_attributes(self):
        r = api.respond('متجر باسم الورد فيه "><b>x 20')
        if r["ok"]:
            self.assertNotIn('"><b>', r["files"]["index.html"])

    def test_it_says_plainly_that_nothing_is_paid(self):
        self.assertIn("لا يوجد دفع إلكتروني", self.html)

    def test_only_a_shop_gets_a_cart_and_payment_is_still_refused(self):
        self.assertTrue(build("ابغى متجر باسم الورد وفيه ورد 20 وسلة مشتريات").ok)
        self.assertIn("غير مدعوم", build("ابغى موقع تعريفي فيه سلة مشتريات").message)
        self.assertIn("غير مدعوم", build("ابغى متجر باسم الورد وفيه ورد 20 وسلة مشتريات ودفع").message)

    def test_asking_a_shop_for_a_cart_says_it_is_already_there(self):
        e = edit.apply(self.r.spec, "اضف سلة مشتريات")
        self.assertFalse(e.changed)
        self.assertIn("موجودة", e.note)

    def test_a_product_called_basket_is_still_a_product(self):
        e = edit.apply(self.r.spec, "اضف منتج سلة 50")
        self.assertTrue(e.changed, e.note)


if __name__ == "__main__":
    unittest.main()
