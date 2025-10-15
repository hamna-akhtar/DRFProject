""" tests for friends views"""

from datetime import date
from rest_framework.test import force_authenticate
from rest_framework import status
from tests.base import CustomBaseTestCase
from friends.models import FriendRequest
from friends import views


class FriendRequestListCreateViewTests(CustomBaseTestCase):
    """tests for FriendRequestListCreateView"""

    def test_friend_request_list_requires_authentication(self):
        """only authenticated users can view friend requests list"""
        view = views.FriendRequestListCreateView.as_view()
        request = self.factory.get("/friends/")

        # without auth
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # with auth
        force_authenticate(request, user=self.user1)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_friend_request_create_requires_authentication(self):
        """only authenticated users can create friend request"""
        view = views.FriendRequestListCreateView.as_view()
        data = {"send_request_to": self.user2.id}
        request = self.factory.post("/friends/", data, format="json")

        # without auth
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # with auth
        force_authenticate(request, user=self.user1)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_friend_request_list_includes_only_my_sent_and_received(self):
        """only show sent and received friend requests of currently authenticated user"""
        sent = FriendRequest.objects.create(
            requested_by=self.user1, requested_to=self.user2
        )
        received = FriendRequest.objects.create(
            requested_by=self.user3, requested_to=self.user1
        )
        other_request = FriendRequest.objects.create(
            requested_by=self.user2, requested_to=self.user3
        )

        request = self.factory.get("/friends/")
        force_authenticate(request, user=self.user1)
        view = views.FriendRequestListCreateView.as_view()
        response = view(request)
        response.render()

        request_ids = [res["id"] for res in response.data]
        self.assertIn(sent.id, request_ids)
        self.assertIn(received.id, request_ids)
        self.assertEqual(len(response.data), 2)
        self.assertNotIn(other_request.id, request_ids)

    def test_friend_request_create_sets_requested_by_and_created_at(self):
        """requested_by and created_at fields are automatically set on friend request creation"""
        data = {"send_request_to": self.user2.id}
        request = self.factory.post("/friends/", data, format="json")
        force_authenticate(request, user=self.user1)
        view = views.FriendRequestListCreateView.as_view()
        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        friend_request = FriendRequest.objects.get(id=response.data["id"])
        self.assertEqual(friend_request.requested_by, self.user1)
        self.assertEqual(friend_request.requested_to, self.user2)
        self.assertEqual(friend_request.created_at, date.today())


class FriendRequestDetailViewTests(CustomBaseTestCase):
    """tests for FriendRequestDetailView"""

    def test_friend_request_detail_requires_authentication(self):
        """only authenticated user can view friend request detail"""
        friend_request = FriendRequest.objects.create(
            requested_by=self.user1, requested_to=self.user2
        )

        view = views.FriendRequestDetailView.as_view()
        request = self.factory.get(f"/friends/{friend_request.id}/")

        # without auth
        response = view(request, pk=friend_request.id)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # with auth
        force_authenticate(request, user=self.user1)
        response = view(request, pk=friend_request.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_friend_request_update_requires_authentication(self):
        """only authenticated user can update friend request"""
        friend_request = FriendRequest.objects.create(
            requested_by=self.user1, requested_to=self.user2
        )

        view = views.FriendRequestDetailView.as_view()
        data = {"accepted": True}
        request = self.factory.put(
            f"/friends/{friend_request.id}/", data, format="json"
        )

        # without auth
        response = view(request, pk=friend_request.id)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # with auth
        force_authenticate(request, user=self.user2)
        response = view(request, pk=friend_request.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_friend_request_only_receiver_can_accept(self):
        """only receiver can accept friend request"""
        friend_request = FriendRequest.objects.create(
            requested_by=self.user1, requested_to=self.user2
        )

        view = views.FriendRequestDetailView.as_view()
        data = {"accepted": True}
        request = self.factory.put(
            f"/friends/{friend_request.id}/", data, format="json"
        )

        # requestor cannot accept
        force_authenticate(request, user=self.user1)
        response = view(request, pk=friend_request.id)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # receiver can accept
        force_authenticate(request, user=self.user2)
        response = view(request, pk=friend_request.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_friend_request_detail_view_by_requester_and_receiver_only(self):
        """only receiver and requestor can view friend request detail"""
        friend_request = FriendRequest.objects.create(
            requested_by=self.user1, requested_to=self.user2
        )
        view = views.FriendRequestDetailView.as_view()

        # requestor can view
        request = self.factory.get(f"/friends/{friend_request.id}/")
        force_authenticate(request, user=self.user1)
        response = view(request, pk=friend_request.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # receiver can view
        request = self.factory.get(f"/friends/{friend_request.id}/")
        force_authenticate(request, user=self.user2)
        response = view(request, pk=friend_request.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # others cannot view
        request = self.factory.get(f"/friends/{friend_request.id}/")
        force_authenticate(request, user=self.user3)
        response = view(request, pk=friend_request.id)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_friend_request_delete_by_requester_and_receiver_only(self):
        """only receiver and requestor can delete friend request"""
        view = views.FriendRequestDetailView.as_view()
        friend_request = FriendRequest.objects.create(
            requested_by=self.user1, requested_to=self.user2
        )
        request = self.factory.delete(f"/friends/{friend_request.id}/")

        # others cannot delete request
        force_authenticate(request, user=self.user3)
        response = view(request, pk=friend_request.id)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # requestor can delete request
        force_authenticate(request, user=self.user1)
        response = view(request, pk=friend_request.id)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # receiver can delete request
        friend_request = FriendRequest.objects.create(
            requested_by=self.user1, requested_to=self.user2
        )
        request = self.factory.delete(f"/friends/{friend_request.id}/")
        force_authenticate(request, user=self.user1)
        response = view(request, pk=friend_request.id)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_friend_request_accept_adds_to_both_friends_lists(self):
        """add users to eachother's friends lists when request is accepted"""
        friend_request = FriendRequest.objects.create(
            requested_by=self.user1, requested_to=self.user2
        )

        data = {"accepted": True}
        request = self.factory.patch(
            f"/friends/{friend_request.id}/", data, format="json"
        )
        force_authenticate(request, user=self.user2)
        view = views.FriendRequestDetailView.as_view()
        response = view(request, pk=friend_request.id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(self.user2, self.user1.friends.all())
        self.assertIn(self.user1, self.user2.friends.all())

    def test_friend_request_unaccept_removes_from_both_friends_lists(self):
        """remove users from eachother's friends lists when request is unaccepted"""
        friend_request = FriendRequest.objects.create(
            requested_by=self.user1, requested_to=self.user2, accepted=True
        )
        self.user1.friends.add(self.user2)

        data = {"accepted": False}
        request = self.factory.patch(
            f"/friends/{friend_request.id}/", data, format="json"
        )
        force_authenticate(request, user=self.user2)
        view = views.FriendRequestDetailView.as_view()
        response = view(request, pk=friend_request.id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn(self.user2, self.user1.friends.all())
        self.assertNotIn(self.user1, self.user2.friends.all())

    def test_friend_request_delete_accepted_removes_from_both_friends_lists(self):
        """remove users from eachother's friends lists when an accepted request is deleted"""
        friend_request = FriendRequest.objects.create(
            requested_by=self.user1, requested_to=self.user2, accepted=True
        )
        self.user1.friends.add(self.user2)

        request = self.factory.delete(f"/friends/{friend_request.id}/")
        force_authenticate(request, user=self.user1)
        view = views.FriendRequestDetailView.as_view()
        response = view(request, pk=friend_request.id)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertNotIn(self.user2, self.user1.friends.all())
        self.assertNotIn(self.user1, self.user2.friends.all())

    def test_friend_request_delete_unaccepted_doesnt_affect_friends(self):
        """users friends lists are unaffected when an unaccepted request is deleted"""
        friend_request = FriendRequest.objects.create(
            requested_by=self.user1, requested_to=self.user2, accepted=False
        )
        self.assertNotIn(self.user1, self.user2.friends.all())
        self.assertNotIn(self.user2, self.user1.friends.all())

        request = self.factory.delete(f"/friends/{friend_request.id}/")
        force_authenticate(request, user=self.user1)
        view = views.FriendRequestDetailView.as_view()
        response = view(request, pk=friend_request.id)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertNotIn(self.user1, self.user2.friends.all())
        self.assertNotIn(self.user2, self.user1.friends.all())


class RequestsSentViewTests(CustomBaseTestCase):
    """tests for RequestsSentView"""

    def test_requests_sent_requires_authentication(self):
        """only authenticated users can see their sent requests"""
        view = views.RequestsSentView.as_view()
        request = self.factory.get("/friend-requests/sent/")

        # without auth
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # with auth
        force_authenticate(request, user=self.user1)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_requests_sent_shows_only_sent_requests(self):
        """only show requests sent by currently authenticated user"""
        sent = FriendRequest.objects.create(
            requested_by=self.user1, requested_to=self.user2
        )
        received = FriendRequest.objects.create(
            requested_by=self.user2, requested_to=self.user1
        )

        request = self.factory.get("/friend-requests/sent/")
        force_authenticate(request, user=self.user1)
        view = views.RequestsSentView.as_view()
        response = view(request)
        response.render()

        request_ids = [res["id"] for res in response.data]
        self.assertIn(sent.id, request_ids)
        self.assertNotIn(received.id, request_ids)

    def test_requests_sent_excludes_accepted_requests(self):
        """list excludes requests accepted by currently authenticated user"""
        pending = FriendRequest.objects.create(
            requested_by=self.user1, requested_to=self.user2, accepted=False
        )
        accepted = FriendRequest.objects.create(
            requested_by=self.user1, requested_to=self.user3, accepted=True
        )

        request = self.factory.get("/friend-requests/sent/")
        force_authenticate(request, user=self.user1)
        view = views.RequestsSentView.as_view()
        response = view(request)
        response.render()

        request_ids = [res["id"] for res in response.data]
        self.assertIn(pending.id, request_ids)
        self.assertNotIn(accepted.id, request_ids)


class RequestsReceivedViewTests(CustomBaseTestCase):
    """tests for RequestsReceivedView"""

    def test_requests_received_requires_authentication(self):
        """only authenticated users can see their received requests"""
        view = views.RequestsReceivedView.as_view()
        request = self.factory.get("/friend-requests/received/")

        # without auth
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # with auth
        force_authenticate(request, user=self.user1)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_requests_received_shows_only_received_requests(self):
        """only show requests received by currently authenticated user"""
        sent = FriendRequest.objects.create(
            requested_by=self.user1, requested_to=self.user2
        )
        received = FriendRequest.objects.create(
            requested_by=self.user2, requested_to=self.user1
        )

        request = self.factory.get("/friend-requests/received/")
        force_authenticate(request, user=self.user1)
        view = views.RequestsReceivedView.as_view()
        response = view(request)
        response.render()

        request_ids = [res["id"] for res in response.data]
        self.assertNotIn(sent.id, request_ids)
        self.assertIn(received.id, request_ids)

    def test_requests_received_excludes_accepted_requests(self):
        """list excludes requests accepted by currently authenticated user"""
        pending = FriendRequest.objects.create(
            requested_by=self.user2, requested_to=self.user1, accepted=False
        )
        accepted = FriendRequest.objects.create(
            requested_by=self.user3, requested_to=self.user1, accepted=True
        )

        request = self.factory.get("/friend-requests/received/")
        force_authenticate(request, user=self.user1)
        view = views.RequestsReceivedView.as_view()
        response = view(request)
        response.render()

        request_ids = [res["id"] for res in response.data]
        self.assertIn(pending.id, request_ids)
        self.assertNotIn(accepted.id, request_ids)
