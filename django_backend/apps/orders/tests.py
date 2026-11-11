from unittest.mock import patch

from django.db import IntegrityError
from django.test import TestCase
from rest_framework.test import APIClient

from apps.orders.models import Order, OrderApplication, OrderDelivery, Review
from apps.users.models import User


class AdminOrderTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.users = {
            role: User.objects.create(username=f"role{role}", role=role)
            for role in range(4)
        }

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(self.users[1])
        self.order = Order.objects.create(title="测试商单", publisher=self.users[1])
        self.base = f"/api/admin/orders/{self.order.id}/"

    def set_status(self, status):
        self.order.status = status
        self.order.save()

    def post(self, path, data=None, status=200):
        response = self.client.post(path, data or {}, format="json")
        self.assertEqual(response.status_code, status, response.data)
        self.assertEqual(response.data["code"], status)
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)
        return response.data["data"]

    def test_create_list_filters_and_pagination(self):
        data = self.post("/api/admin/orders/", {
            "title": "新商单", "brief": "简介", "requirement": "要求",
            "category": "短剧", "budget": "1000",
        })["order"]
        self.assertEqual(data["status"], Order.DRAFT)
        self.assertEqual(data["publisher"], self.users[1].id)
        response = self.client.get("/api/admin/orders/", {
            "status": "0", "category": "短剧", "search": "新", "page_size": 1,
        })
        page = response.data["data"]
        self.assertEqual(set(page), {"count", "next", "previous", "results"})
        self.assertEqual(page["count"], 1)
        self.assertEqual(page["results"][0]["id"], data["id"])
        response = self.client.get("/api/admin/orders/", {"page_size": 1})
        self.assertIsNotNone(response.data["data"]["next"])
        response = self.client.get("/api/admin/orders/", {"page_size": 1, "page": 2})
        self.assertIsNotNone(response.data["data"]["previous"])
        for status in ("bad", "99"):
            self.assertEqual(self.client.get("/api/admin/orders/", {"status": status}).status_code, 400)
        self.assertEqual(self.client.get("/api/admin/orders/?page=999").status_code, 404)

    def test_input_validation_and_mass_assignment(self):
        for payload in ({}, {"title": " "}, {"title": "x" * 101},
                        {"title": "x", "category": "x" * 33},
                        {"title": "x", "budget": "x" * 33},
                        {"title": "x", "status": 3},
                        {"title": "x", "publisher": self.users[0].id},
                        {"title": "x", "brief": None}):
            self.post("/api/admin/orders/", payload, status=400)
        for payload in ({"title": ""}, {"status": 3}):
            self.assertEqual(self.client.patch(self.base, payload, format="json").status_code, 400)

    def test_detail_includes_applications_and_deliveries(self):
        application = OrderApplication.objects.create(order=self.order, creator=self.users[3], proposal="报名")
        delivery = OrderDelivery.objects.create(order=self.order, creator=self.users[3], video_url="https://example.com/v")
        self.client.force_authenticate(self.users[2])
        data = self.client.get(self.base).data["data"]["order"]
        self.assertEqual(data["applications"][0]["id"], application.id)
        self.assertEqual(data["deliveries"][0]["id"], delivery.id)
        self.assertEqual(data["deliveries"][0]["video_url"], "https://example.com/v")

    def test_role_permissions_for_all_endpoints(self):
        application = OrderApplication.objects.create(order=self.order, creator=self.users[3])
        delivery = OrderDelivery.objects.create(order=self.order, creator=self.users[3])
        operations = [
            ("get", "/api/admin/orders/", (0, 1)),
            ("post", "/api/admin/orders/", (0, 1)),
            ("get", self.base, (0, 1, 2)),
            ("patch", self.base, (0, 1)),
            ("post", self.base + "submit/", (0, 1)),
            ("post", self.base + "complete/", (0, 1)),
            ("post", self.base + "close/", (0, 1)),
            ("get", self.base + "applications/", (0, 1)),
            ("post", self.base + f"applications/{application.id}/select/", (0, 1)),
            ("post", self.base + "review/", (0, 2)),
            ("get", "/api/admin/reviews/deliveries/", (0, 2)),
            ("post", f"/api/admin/deliveries/{delivery.id}/review/", (0, 2)),
        ]
        for role in (None, 0, 1, 2, 3):
            self.client = APIClient()
            if role is not None:
                self.client.force_authenticate(self.users[role])
            for method, url, allowed in operations:
                with self.subTest(role=role, method=method, url=url):
                    self.set_status(Order.DRAFT)
                    response = getattr(self.client, method)(url)
                    if role not in allowed:
                        self.assertEqual(response.status_code, 403, response.data)
                        self.assertEqual(response.data["code"], 403)
                    else:
                        self.assertNotEqual(response.status_code, 403, response.data)

    def test_edit_and_submit_state_matrix(self):
        for status in range(7):
            with self.subTest(status=status):
                self.set_status(status)
                editable = status in (Order.DRAFT, Order.REJECTED)
                response = self.client.patch(self.base, {"brief": "修改"}, format="json")
                self.assertEqual(response.status_code, 200 if editable else 400)
                self.post(self.base + "submit/", status=200 if editable else 400)
                self.order.refresh_from_db()
                self.assertEqual(self.order.status, Order.PENDING if editable else status)

    def test_order_review_reject_resubmit_approve_and_duplicate(self):
        self.post(self.base + "submit/")
        self.client.force_authenticate(self.users[2])
        for payload in ({"action": "reject"}, {"action": "bad"},
                        {"action": "reject", "opinion": " "},
                        {"action": "approve", "opinion": []}):
            self.post(self.base + "review/", payload, status=400)
        self.post(self.base + "review/", {"action": "reject", "opinion": " 补充要求 "})
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.REJECTED)
        review = Review.objects.get(target_type=Review.ORDER)
        self.assertEqual(review.opinion, "补充要求")
        self.assertEqual(review.action, Review.REJECT)
        self.assertEqual(review.reviewer_id, self.users[2].id)
        self.post(self.base + "review/", {"action": "approve"}, status=400)
        self.client.force_authenticate(self.users[1])
        self.post(self.base + "submit/")
        self.client.force_authenticate(self.users[2])
        self.post(self.base + "review/", {"action": "approve"})
        self.post(self.base + "review/", {"action": "reject", "opinion": "重复"}, status=400)
        self.assertEqual(Review.objects.filter(target_type=Review.ORDER).count(), 2)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.ONLINE)

    def test_review_only_pending(self):
        self.client.force_authenticate(self.users[2])
        for status in (0, 2, 3, 4, 5, 6):
            self.set_status(status)
            self.post(self.base + "review/", {"action": "approve"}, status=400)
        self.assertFalse(Review.objects.exists())

    def test_select_multiple_applications_and_wrong_order(self):
        applications = [OrderApplication.objects.create(order=self.order, creator=self.users[r]) for r in (0, 3)]
        url = self.base + f"applications/{applications[0].id}/select/"
        for status in (0, 1, 2, 5, 6):
            self.set_status(status)
            self.post(url, status=400)
        self.set_status(Order.ONLINE)
        self.post(url)
        self.post(url, status=400)
        self.post(self.base + f"applications/{applications[1].id}/select/")
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.PROGRESS)
        self.assertEqual(self.order.applications.filter(selected=True).count(), 2)
        data = self.client.get(self.base + "applications/").data["data"]
        self.assertEqual(len(data["applications"]), 2)
        other = Order.objects.create(title="其他", publisher=self.users[1], status=Order.ONLINE)
        self.post(f"/api/admin/orders/{other.id}/applications/{applications[0].id}/select/", status=404)
        self.post(self.base + "applications/999999/select/", status=404)

    def test_complete_requires_progress_and_approved_delivery(self):
        other = Order.objects.create(title="其他", publisher=self.users[1], status=Order.PROGRESS)
        OrderDelivery.objects.create(order=other, creator=self.users[3], status=OrderDelivery.APPROVED)
        self.set_status(Order.PROGRESS)
        self.post(self.base + "complete/", status=400)
        delivery = OrderDelivery.objects.create(order=self.order, creator=self.users[3])
        for status in (OrderDelivery.PENDING, OrderDelivery.RETURNED):
            delivery.status = status
            delivery.save()
            self.post(self.base + "complete/", status=400)
        delivery.status = OrderDelivery.APPROVED
        delivery.save()
        for status in (0, 1, 2, 3, 5, 6):
            self.set_status(status)
            self.post(self.base + "complete/", status=400)
        self.set_status(Order.PROGRESS)
        self.post(self.base + "complete/")
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.COMPLETED)
        self.post(self.base + "complete/", status=400)
        self.post(self.base + "close/", status=400)

    def test_close_non_terminal_states_only(self):
        for status in range(7):
            self.set_status(status)
            self.post(self.base + "close/", status=200 if status < 5 else 400)
            self.order.refresh_from_db()
            self.assertEqual(self.order.status, Order.CLOSED if status < 5 else status)

    def test_delivery_review_and_duplicate(self):
        self.set_status(Order.PROGRESS)
        self.client.force_authenticate(self.users[2])
        for action, expected in (("approve", OrderDelivery.APPROVED), ("reject", OrderDelivery.RETURNED)):
            delivery = OrderDelivery.objects.create(order=self.order, creator=self.users[3])
            url = f"/api/admin/deliveries/{delivery.id}/review/"
            self.post(url, {"action": "reject", "opinion": " "}, status=400)
            self.post(url, {"action": "invalid"}, status=400)
            self.post(url, {"action": action, "opinion": "审核意见"})
            delivery.refresh_from_db()
            self.assertEqual(delivery.status, expected)
            self.post(url, {"action": "approve"}, status=400)
            self.post(url, {"action": "reject", "opinion": "重复"}, status=400)
            self.assertEqual(Review.objects.filter(target_type=Review.DELIVERY, target_id=delivery.id).count(), 1)
        pending = OrderDelivery.objects.create(order=self.order, creator=self.users[3])
        data = self.client.get("/api/admin/reviews/deliveries/").data["data"]
        self.assertEqual([d["id"] for d in data["deliveries"]], [pending.id])
        for status in (0, 1, 2, 3, 5, 6):
            self.set_status(status)
            self.post(f"/api/admin/deliveries/{pending.id}/review/", {"action": "approve"}, status=400)

    def test_review_failure_rolls_back_order_and_delivery(self):
        self.client.force_authenticate(self.users[2])
        self.set_status(Order.PENDING)
        with patch("apps.orders.views.Review.objects.create", side_effect=IntegrityError("audit failure")):
            self.post(self.base + "review/", {"action": "approve"}, status=500)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.PENDING)
        self.set_status(Order.PROGRESS)
        delivery = OrderDelivery.objects.create(order=self.order, creator=self.users[3])
        with patch("apps.orders.views.Review.objects.create", side_effect=IntegrityError("audit failure")):
            self.post(f"/api/admin/deliveries/{delivery.id}/review/", {"action": "approve"}, status=500)
        delivery.refresh_from_db()
        self.assertEqual(delivery.status, OrderDelivery.PENDING)
        self.assertFalse(Review.objects.exists())

    def test_selection_failure_rolls_back_application(self):
        self.set_status(Order.ONLINE)
        application = OrderApplication.objects.create(order=self.order, creator=self.users[3])
        with patch("apps.orders.views.Order.save", side_effect=IntegrityError("save failure")):
            self.post(self.base + f"applications/{application.id}/select/", status=500)
        application.refresh_from_db()
        self.order.refresh_from_db()
        self.assertFalse(application.selected)
        self.assertEqual(self.order.status, Order.ONLINE)

    def test_missing_resources(self):
        missing = "/api/admin/orders/999999/"
        self.assertEqual(self.client.get(missing).status_code, 404)
        self.assertEqual(self.client.patch(missing, {"title": "x"}, format="json").status_code, 404)
        self.assertEqual(self.client.get(missing + "applications/").status_code, 404)
        for action in ("submit", "complete", "close", "applications/999/select"):
            self.post(missing + action + "/", status=404)
        self.client.force_authenticate(self.users[2])
        self.post(missing + "review/", {"action": "approve"}, status=404)
        self.post("/api/admin/deliveries/999999/review/", {"action": "approve"}, status=404)

    def test_full_admin_workflow(self):
        self.post(self.base + "submit/")
        self.client.force_authenticate(self.users[2])
        self.post(self.base + "review/", {"action": "approve"})
        application = OrderApplication.objects.create(order=self.order, creator=self.users[3])
        self.client.force_authenticate(self.users[1])
        self.post(self.base + f"applications/{application.id}/select/")
        # 前台报名和上传不在本次范围，按既有模型构造交付记录。
        returned = OrderDelivery.objects.create(order=self.order, creator=self.users[3], delivery_type=OrderDelivery.VIDEO)
        self.client.force_authenticate(self.users[2])
        self.post(f"/api/admin/deliveries/{returned.id}/review/", {"action": "reject", "opinion": "请修改"})
        approved = OrderDelivery.objects.create(order=self.order, creator=self.users[3], delivery_type=OrderDelivery.LINK, video_url="https://example.com/video")
        self.post(f"/api/admin/deliveries/{approved.id}/review/", {"action": "approve"})
        self.client.force_authenticate(self.users[1])
        self.post(self.base + "complete/")
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.COMPLETED)
        self.assertEqual(Review.objects.count(), 3)
