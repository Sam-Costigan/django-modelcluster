from __future__ import unicode_literals

import datetime
import itertools

from django.test import TestCase
from django.db import IntegrityError

from modelcluster.models import get_all_child_relations
from modelcluster.queryset import FakeQuerySet

from tests.models import Band, BandMember, Place, Restaurant, SeafoodRestaurant, Review, Album, \
    Article, Author, Category, Person, Room, House, Log


class ClusterTest(TestCase):
    def test_can_create_cluster(self):
        beatles = Band(name='The Beatles')

        self.assertEqual(0, beatles.members.count())

        beatles.members = [
            BandMember(name='John Lennon'),
            BandMember(name='Paul McCartney'),
        ]

        # we should be able to query this relation using (some) queryset methods
        self.assertEqual(2, beatles.members.count())
        self.assertEqual('John Lennon', beatles.members.all()[0].name)

        self.assertEqual('Paul McCartney', beatles.members.filter(name='Paul McCartney')[0].name)
        self.assertEqual('Paul McCartney', beatles.members.filter(name__exact='Paul McCartney')[0].name)
        self.assertEqual('Paul McCartney', beatles.members.filter(name__iexact='paul mccartNEY')[0].name)

        self.assertEqual(0, beatles.members.filter(name__lt='B').count())
        self.assertEqual(1, beatles.members.filter(name__lt='M').count())
        self.assertEqual('John Lennon', beatles.members.filter(name__lt='M')[0].name)
        self.assertEqual(1, beatles.members.filter(name__lt='Paul McCartney').count())
        self.assertEqual('John Lennon', beatles.members.filter(name__lt='Paul McCartney')[0].name)
        self.assertEqual(2, beatles.members.filter(name__lt='Z').count())

        self.assertEqual(0, beatles.members.filter(name__lte='B').count())
        self.assertEqual(1, beatles.members.filter(name__lte='M').count())
        self.assertEqual('John Lennon', beatles.members.filter(name__lte='M')[0].name)
        self.assertEqual(2, beatles.members.filter(name__lte='Paul McCartney').count())
        self.assertEqual(2, beatles.members.filter(name__lte='Z').count())

        self.assertEqual(2, beatles.members.filter(name__gt='B').count())
        self.assertEqual(1, beatles.members.filter(name__gt='M').count())
        self.assertEqual('Paul McCartney', beatles.members.filter(name__gt='M')[0].name)
        self.assertEqual(0, beatles.members.filter(name__gt='Paul McCartney').count())

        self.assertEqual(2, beatles.members.filter(name__gte='B').count())
        self.assertEqual(1, beatles.members.filter(name__gte='M').count())
        self.assertEqual('Paul McCartney', beatles.members.filter(name__gte='M')[0].name)
        self.assertEqual(1, beatles.members.filter(name__gte='Paul McCartney').count())
        self.assertEqual('Paul McCartney', beatles.members.filter(name__gte='Paul McCartney')[0].name)
        self.assertEqual(0, beatles.members.filter(name__gte='Z').count())

        self.assertEqual(1, beatles.members.filter(name__contains='Cart').count())
        self.assertEqual('Paul McCartney', beatles.members.filter(name__contains='Cart')[0].name)
        self.assertEqual(1, beatles.members.filter(name__icontains='carT').count())
        self.assertEqual('Paul McCartney', beatles.members.filter(name__icontains='carT')[0].name)

        self.assertEqual(1, beatles.members.filter(name__in=['Paul McCartney', 'Linda McCartney']).count())
        self.assertEqual('Paul McCartney', beatles.members.filter(name__in=['Paul McCartney', 'Linda McCartney'])[0].name)

        self.assertEqual(1, beatles.members.filter(name__startswith='Paul').count())
        self.assertEqual('Paul McCartney', beatles.members.filter(name__startswith='Paul')[0].name)
        self.assertEqual(1, beatles.members.filter(name__istartswith='pauL').count())
        self.assertEqual('Paul McCartney', beatles.members.filter(name__istartswith='pauL')[0].name)
        self.assertEqual(1, beatles.members.filter(name__endswith='ney').count())
        self.assertEqual('Paul McCartney', beatles.members.filter(name__endswith='ney')[0].name)
        self.assertEqual(1, beatles.members.filter(name__iendswith='Ney').count())
        self.assertEqual('Paul McCartney', beatles.members.filter(name__iendswith='Ney')[0].name)

        self.assertEqual('Paul McCartney', beatles.members.get(name='Paul McCartney').name)
        self.assertEqual('Paul McCartney', beatles.members.get(name__exact='Paul McCartney').name)
        self.assertEqual('Paul McCartney', beatles.members.get(name__iexact='paul mccartNEY').name)
        self.assertEqual('John Lennon', beatles.members.get(name__lt='Paul McCartney').name)
        self.assertEqual('John Lennon', beatles.members.get(name__lte='M').name)
        self.assertEqual('Paul McCartney', beatles.members.get(name__gt='M').name)
        self.assertEqual('Paul McCartney', beatles.members.get(name__gte='Paul McCartney').name)
        self.assertEqual('Paul McCartney', beatles.members.get(name__contains='Cart').name)
        self.assertEqual('Paul McCartney', beatles.members.get(name__icontains='carT').name)
        self.assertEqual('Paul McCartney', beatles.members.get(name__in=['Paul McCartney', 'Linda McCartney']).name)
        self.assertEqual('Paul McCartney', beatles.members.get(name__startswith='Paul').name)
        self.assertEqual('Paul McCartney', beatles.members.get(name__istartswith='pauL').name)
        self.assertEqual('Paul McCartney', beatles.members.get(name__endswith='ney').name)
        self.assertEqual('Paul McCartney', beatles.members.get(name__iendswith='Ney').name)

        self.assertEqual('John Lennon', beatles.members.get(name__regex=r'n{2}').name)
        self.assertEqual('John Lennon', beatles.members.get(name__iregex=r'N{2}').name)

        self.assertRaises(BandMember.DoesNotExist, lambda: beatles.members.get(name='Reginald Dwight'))
        self.assertRaises(BandMember.MultipleObjectsReturned, lambda: beatles.members.get())

        self.assertEqual([('Paul McCartney',)], beatles.members.filter(name='Paul McCartney').values_list('name'))
        self.assertEqual(['Paul McCartney'], beatles.members.filter(name='Paul McCartney').values_list('name', flat=True))
        # quick-and-dirty check that we can invoke values_list with empty args list
        beatles.members.filter(name='Paul McCartney').values_list()

        self.assertTrue(beatles.members.filter(name='Paul McCartney').exists())
        self.assertFalse(beatles.members.filter(name='Reginald Dwight').exists())

        self.assertEqual('John Lennon', beatles.members.first().name)
        self.assertEqual('Paul McCartney', beatles.members.last().name)

        self.assertTrue('John Lennon', beatles.members.order_by('name').first())
        self.assertTrue('Paul McCartney', beatles.members.order_by('-name').first())

        # these should not exist in the database yet
        self.assertFalse(Band.objects.filter(name='The Beatles').exists())
        self.assertFalse(BandMember.objects.filter(name='John Lennon').exists())

        beatles.save()
        # this should create database entries
        self.assertTrue(Band.objects.filter(name='The Beatles').exists())
        self.assertTrue(BandMember.objects.filter(name='John Lennon').exists())

        john_lennon = BandMember.objects.get(name='John Lennon')
        beatles.members = [john_lennon]
        # reassigning should take effect on the in-memory record
        self.assertEqual(1, beatles.members.count())
        # but not the database
        self.assertEqual(2, Band.objects.get(name='The Beatles').members.count())

        beatles.save()
        # now updated in the database
        self.assertEqual(1, Band.objects.get(name='The Beatles').members.count())
        self.assertEqual(1, BandMember.objects.filter(name='John Lennon').count())
        # removed member should be deleted from the db entirely
        self.assertEqual(0, BandMember.objects.filter(name='Paul McCartney').count())

        # queries on beatles.members should now revert to SQL
        self.assertTrue(beatles.members.extra(where=["tests_bandmember.name='John Lennon'"]).exists())

    def test_related_manager_assignment_ops(self):
        beatles = Band(name='The Beatles')
        john = BandMember(name='John Lennon')
        paul = BandMember(name='Paul McCartney')

        beatles.members.add(john)
        self.assertEqual(1, beatles.members.count())

        beatles.members.add(paul)
        self.assertEqual(2, beatles.members.count())
        # ensure that duplicates are filtered
        beatles.members.add(paul)
        self.assertEqual(2, beatles.members.count())

        beatles.members.remove(john)
        self.assertEqual(1, beatles.members.count())
        self.assertEqual(paul, beatles.members.all()[0])

        george = beatles.members.create(name='George Harrison')
        self.assertEqual(2, beatles.members.count())
        self.assertEqual('George Harrison', george.name)

        beatles.members.set([john])
        self.assertEqual(1, beatles.members.count())
        self.assertEqual(john, beatles.members.all()[0])

    def test_can_pass_child_relations_as_constructor_kwargs(self):
        beatles = Band(name='The Beatles', members=[
            BandMember(name='John Lennon'),
            BandMember(name='Paul McCartney'),
        ])
        self.assertEqual(2, beatles.members.count())
        self.assertEqual(beatles, beatles.members.all()[0].band)

    def test_can_access_child_relations_of_superclass(self):
        fat_duck = Restaurant(name='The Fat Duck', serves_hot_dogs=False, reviews=[
            Review(author='Michael Winner', body='Rubbish.')
        ])
        self.assertEqual(1, fat_duck.reviews.count())
        self.assertEqual(fat_duck.reviews.first().author, 'Michael Winner')
        self.assertEqual(fat_duck, fat_duck.reviews.all()[0].place)

        fat_duck.save()
        # ensure relations have been saved to the database
        fat_duck = Restaurant.objects.get(id=fat_duck.id)
        self.assertEqual(1, fat_duck.reviews.count())
        self.assertEqual(fat_duck.reviews.first().author, 'Michael Winner')

    def test_can_only_commit_on_saved_parent(self):
        beatles = Band(name='The Beatles', members=[
            BandMember(name='John Lennon'),
            BandMember(name='Paul McCartney'),
        ])
        self.assertRaises(IntegrityError, lambda: beatles.members.commit())

        beatles.save()
        beatles.members.commit()

    def test_integrity_error_with_none_pk(self):
        beatles = Band(name='The Beatles', members=[
            BandMember(name='John Lennon'),
            BandMember(name='Paul McCartney'),
        ])
        beatles.save()
        beatles.pk = None
        self.assertRaises(IntegrityError, lambda: beatles.members.commit())
        # this should work fine, as Django will end up cloning this entity
        beatles.save()
        self.assertEqual(Band.objects.get(pk=beatles.pk).name, 'The Beatles')

    def test_model_with_zero_pk(self):
        beatles = Band(name='The Beatles', members=[
            BandMember(name='John Lennon'),
            BandMember(name='Paul McCartney'),
        ])
        beatles.save()
        beatles.pk = 0
        beatles.members.commit()
        beatles.save()
        self.assertEqual(Band.objects.get(pk=0).name, 'The Beatles')

    def test_save_with_update_fields(self):
        beatles = Band(name='The Beatles', members=[
            BandMember(name='John Lennon'),
            BandMember(name='Paul McCartney'),
        ], albums=[
            Album(name='Please Please Me', sort_order=1),
            Album(name='With The Beatles', sort_order=2),
            Album(name='Abbey Road', sort_order=3),
        ])

        beatles.save()

        # modify both relations, but only commit the change to members
        beatles.members.clear()
        beatles.albums.clear()
        beatles.name = 'The Rutles'
        beatles.save(update_fields=['name', 'members'])

        updated_beatles = Band.objects.get(pk=beatles.pk)
        self.assertEqual(updated_beatles.name, 'The Rutles')
        self.assertEqual(updated_beatles.members.count(), 0)
        self.assertEqual(updated_beatles.albums.count(), 3)

    def test_queryset_filtering(self):
        beatles = Band(name='The Beatles', members=[
            BandMember(id=1, name='John Lennon'),
            BandMember(id=2, name='Paul McCartney'),
        ])
        self.assertEqual('Paul McCartney', beatles.members.get(id=2).name)
        self.assertEqual('Paul McCartney', beatles.members.get(id='2').name)
        self.assertEqual(1, beatles.members.filter(name='Paul McCartney').count())

        # also need to be able to filter on foreign fields that return a model instance
        # rather than a simple python value
        self.assertEqual(2, beatles.members.filter(band=beatles).count())
        # and ensure that the comparison is not treating all unsaved instances as identical
        rutles = Band(name='The Rutles')
        self.assertEqual(0, beatles.members.filter(band=rutles).count())

        # and the comparison must be on the model instance's ID where available,
        # not by reference
        beatles.save()
        beatles.members.add(BandMember(id=3, name='George Harrison'))  # modify the relation so that we're not to a plain database-backed queryset

        also_beatles = Band.objects.get(id=beatles.id)
        self.assertEqual(3, beatles.members.filter(band=also_beatles).count())

    def test_queryset_filtering_on_models_with_inheritance(self):
        strawberry_fields = Restaurant.objects.create(name='Strawberry Fields')
        the_yellow_submarine = SeafoodRestaurant.objects.create(name='The Yellow Submarine')

        john = BandMember(name='John Lennon', favourite_restaurant=strawberry_fields)
        ringo = BandMember(name='Ringo Starr', favourite_restaurant=Restaurant.objects.get(name='The Yellow Submarine'))

        beatles = Band(name='The Beatles', members=[john, ringo])

        # queried instance is less specific
        self.assertEqual(
            list(beatles.members.filter(favourite_restaurant=Place.objects.get(name='Strawberry Fields'))),
            [john]
        )

        # queried instance is more specific
        self.assertEqual(
            list(beatles.members.filter(favourite_restaurant=the_yellow_submarine)),
            [ringo]
        )

    def test_queryset_exclude_filtering(self):
        beatles = Band(name='The Beatles', members=[
            BandMember(id=1, name='John Lennon'),
            BandMember(id=2, name='Paul McCartney'),
        ])

        self.assertEqual(1, beatles.members.exclude(name='Paul McCartney').count())
        self.assertEqual('John Lennon', beatles.members.exclude(name='Paul McCartney').first().name)

        self.assertEqual(1, beatles.members.exclude(name__exact='Paul McCartney').count())
        self.assertEqual('John Lennon', beatles.members.exclude(name__exact='Paul McCartney').first().name)
        self.assertEqual(1, beatles.members.exclude(name__iexact='paul mccartNEY').count())
        self.assertEqual('John Lennon', beatles.members.exclude(name__iexact='paul mccartNEY').first().name)

        self.assertEqual(1, beatles.members.exclude(name__lt='M').count())
        self.assertEqual('Paul McCartney', beatles.members.exclude(name__lt='M').first().name)
        self.assertEqual(1, beatles.members.exclude(name__lt='Paul McCartney').count())
        self.assertEqual('Paul McCartney', beatles.members.exclude(name__lt='Paul McCartney').first().name)

        self.assertEqual(1, beatles.members.exclude(name__lte='John Lennon').count())
        self.assertEqual('Paul McCartney', beatles.members.exclude(name__lte='John Lennon').first().name)

        self.assertEqual(1, beatles.members.exclude(name__gt='M').count())
        self.assertEqual('John Lennon', beatles.members.exclude(name__gt='M').first().name)
        self.assertEqual(1, beatles.members.exclude(name__gte='Paul McCartney').count())
        self.assertEqual('John Lennon', beatles.members.exclude(name__gte='Paul McCartney').first().name)

        self.assertEqual(1, beatles.members.exclude(name__contains='Cart').count())
        self.assertEqual('John Lennon', beatles.members.exclude(name__contains='Cart').first().name)
        self.assertEqual(1, beatles.members.exclude(name__icontains='carT').count())
        self.assertEqual('John Lennon', beatles.members.exclude(name__icontains='carT').first().name)

        self.assertEqual(1, beatles.members.exclude(name__in=['Paul McCartney', 'Linda McCartney']).count())
        self.assertEqual('John Lennon', beatles.members.exclude(name__in=['Paul McCartney', 'Linda McCartney'])[0].name)

        self.assertEqual(1, beatles.members.exclude(name__startswith='Paul').count())
        self.assertEqual('John Lennon', beatles.members.exclude(name__startswith='Paul').first().name)
        self.assertEqual(1, beatles.members.exclude(name__istartswith='pauL').count())
        self.assertEqual('John Lennon', beatles.members.exclude(name__istartswith='pauL').first().name)
        self.assertEqual(1, beatles.members.exclude(name__endswith='ney').count())
        self.assertEqual('John Lennon', beatles.members.exclude(name__endswith='ney').first().name)
        self.assertEqual(1, beatles.members.exclude(name__iendswith='Ney').count())
        self.assertEqual('John Lennon', beatles.members.exclude(name__iendswith='Ney').first().name)

    def test_queryset_filter_with_nulls(self):
        tmbg = Band(name="They Might Be Giants", albums=[
            Album(name="Flood", release_date=datetime.date(1990, 1, 1)),
            Album(name="John Henry", release_date=datetime.date(1994, 7, 21)),
            Album(name="Factory Showroom", release_date=datetime.date(1996, 3, 30)),
            Album(name="", release_date=None),
            Album(name=None, release_date=None),
        ])

        self.assertEqual(tmbg.albums.get(name="Flood").name, "Flood")
        self.assertEqual(tmbg.albums.get(name="").name, "")
        self.assertEqual(tmbg.albums.get(name=None).name, None)

        self.assertEqual(tmbg.albums.get(name__exact="Flood").name, "Flood")
        self.assertEqual(tmbg.albums.get(name__exact="").name, "")
        self.assertEqual(tmbg.albums.get(name__exact=None).name, None)

        self.assertEqual(tmbg.albums.get(name__iexact="flood").name, "Flood")
        self.assertEqual(tmbg.albums.get(name__iexact="").name, "")
        self.assertEqual(tmbg.albums.get(name__iexact=None).name, None)

        self.assertEqual(tmbg.albums.get(name__contains="loo").name, "Flood")
        self.assertEqual(tmbg.albums.get(name__icontains="LOO").name, "Flood")
        self.assertEqual(tmbg.albums.get(name__startswith="Flo").name, "Flood")
        self.assertEqual(tmbg.albums.get(name__istartswith="flO").name, "Flood")
        self.assertEqual(tmbg.albums.get(name__endswith="ood").name, "Flood")
        self.assertEqual(tmbg.albums.get(name__iendswith="Ood").name, "Flood")

        self.assertEqual(tmbg.albums.get(name__lt="A").name, "")
        self.assertEqual(tmbg.albums.get(name__lte="A").name, "")
        self.assertEqual(tmbg.albums.get(name__gt="J").name, "John Henry")
        self.assertEqual(tmbg.albums.get(name__gte="J").name, "John Henry")

        self.assertEqual(tmbg.albums.get(name__in=["Flood", "Mink Car"]).name, "Flood")
        self.assertEqual(tmbg.albums.get(name__in=["", "Mink Car"]).name, "")
        self.assertEqual(tmbg.albums.get(name__in=[None, "Mink Car"]).name, None)

        self.assertEqual(tmbg.albums.filter(name__isnull=True).count(), 1)
        self.assertEqual(tmbg.albums.filter(name__isnull=False).count(), 4)

        self.assertEqual(tmbg.albums.get(name__regex=r'l..d').name, "Flood")
        self.assertEqual(tmbg.albums.get(name__iregex=r'f..o').name, "Flood")

    def test_date_filters(self):
        tmbg = Band(name="They Might Be Giants", albums=[
            Album(name="Flood", release_date=datetime.date(1990, 1, 1)),
            Album(name="John Henry", release_date=datetime.date(1994, 7, 21)),
            Album(name="Factory Showroom", release_date=datetime.date(1996, 3, 30)),
            Album(name="The Complete Dial-A-Song", release_date=None),
        ])

        logs = FakeQuerySet(Log, [
            Log(time=datetime.datetime(1979, 7, 1, 1, 1, 1), data="nobody died"),
            Log(time=datetime.datetime(1980, 2, 2, 2, 2, 2), data="one person died"),
            Log(time=None, data="nothing happened")
        ])

        self.assertEqual(
            tmbg.albums.get(release_date__range=(datetime.date(1994, 1, 1), datetime.date(1994, 12, 31))).name,
            "John Henry"
        )
        self.assertEqual(
            logs.get(time__range=(datetime.datetime(1980, 1, 1, 1, 1, 1), datetime.datetime(1980, 12, 31, 23, 59, 59))).data,
            "one person died"
        )

        self.assertEqual(
            tmbg.albums.get(release_date__date=datetime.date(1994, 7, 21)).name,
            "John Henry"
        )
        self.assertEqual(
            logs.get(time__date=datetime.date(1980, 2, 2)).data,
            "one person died"
        )

        self.assertEqual(
            tmbg.albums.get(release_date__year='1994').name,
            "John Henry"
        )
        self.assertEqual(
            logs.get(time__year=1980).data,
            "one person died"
        )

        self.assertEqual(
            tmbg.albums.get(release_date__month=7).name,
            "John Henry"
        )
        self.assertEqual(
            logs.get(time__month='2').data,
            "one person died"
        )

        self.assertEqual(
            tmbg.albums.get(release_date__day='21').name,
            "John Henry"
        )
        self.assertEqual(
            logs.get(time__day=2).data,
            "one person died"
        )

        self.assertEqual(
            tmbg.albums.get(release_date__week=29).name,
            "John Henry"
        )
        self.assertEqual(
            logs.get(time__week='5').data,
            "one person died"
        )

        self.assertEqual(
            tmbg.albums.get(release_date__week_day=5).name,
            "John Henry"
        )
        self.assertEqual(
            logs.get(time__week_day=7).data,
            "one person died"
        )

        self.assertEqual(
            tmbg.albums.get(release_date__quarter=3).name,
            "John Henry"
        )
        self.assertEqual(
            logs.get(time__quarter=1).data,
            "one person died"
        )

        self.assertEqual(
            logs.get(time__time=datetime.time(2, 2, 2)).data,
            "one person died"
        )

        self.assertEqual(
            logs.get(time__hour=2).data,
            "one person died"
        )

        self.assertEqual(
            logs.get(time__minute='2').data,
            "one person died"
        )

        self.assertEqual(
            logs.get(time__second=2).data,
            "one person died"
        )

    def test_prefetch_related(self):
        Band.objects.create(name='The Beatles', members=[
            BandMember(id=1, name='John Lennon'),
            BandMember(id=2, name='Paul McCartney'),
        ])
        with self.assertNumQueries(2):
            lists = [list(band.members.all()) for band in Band.objects.prefetch_related('members')]
        normal_lists = [list(band.members.all()) for band in Band.objects.all()]
        self.assertEqual(lists, normal_lists)

    def test_prefetch_related_with_custom_queryset(self):
        from django.db.models import Prefetch
        Band.objects.create(name='The Beatles', members=[
            BandMember(id=1, name='John Lennon'),
            BandMember(id=2, name='Paul McCartney'),
        ])
        with self.assertNumQueries(2):
            lists = [
                list(band.members.all())
                for band in Band.objects.prefetch_related(
                    Prefetch('members', queryset=BandMember.objects.filter(name__startswith='Paul'))
                )
            ]
        normal_lists = [list(band.members.filter(name__startswith='Paul')) for band in Band.objects.all()]
        self.assertEqual(lists, normal_lists)

    def test_order_by_with_multiple_fields(self):
        beatles = Band(name='The Beatles', albums=[
            Album(name='Please Please Me', sort_order=2),
            Album(name='With The Beatles', sort_order=1),
            Album(name='Abbey Road', sort_order=2),
        ])

        albums = [album.name for album in beatles.albums.order_by('sort_order', 'name')]
        self.assertEqual(['With The Beatles', 'Abbey Road', 'Please Please Me'], albums)

        albums = [album.name for album in beatles.albums.order_by('sort_order', '-name')]
        self.assertEqual(['With The Beatles', 'Please Please Me', 'Abbey Road'], albums)

    def test_meta_ordering(self):
        beatles = Band(name='The Beatles', albums=[
            Album(name='Please Please Me', sort_order=2),
            Album(name='With The Beatles', sort_order=1),
            Album(name='Abbey Road', sort_order=3),
        ])

        # in the absence of an explicit order_by clause, it should use the ordering as defined
        # in Album.Meta, which is 'sort_order'
        albums = [album.name for album in beatles.albums.all()]
        self.assertEqual(['With The Beatles', 'Please Please Me', 'Abbey Road'], albums)

    def test_parental_key_checks_clusterable_model(self):
        from django.core import checks
        from django.db import models
        from modelcluster.fields import ParentalKey

        class Instrument(models.Model):
            # Oops, BandMember is not a Clusterable model
            member = ParentalKey(BandMember, on_delete=models.CASCADE)

            class Meta:
                # Prevent Django from thinking this is in the database
                # This shouldn't affect the test
                abstract = True

        # Check for error
        errors = Instrument.check()
        self.assertEqual(1, len(errors))

        # Check the error itself
        error = errors[0]
        self.assertIsInstance(error, checks.Error)
        self.assertEqual(error.id, 'modelcluster.E001')
        self.assertEqual(error.obj, Instrument.member.field)
        self.assertEqual(error.msg, 'ParentalKey must point to a subclass of ClusterableModel.')
        self.assertEqual(error.hint, 'Change tests.BandMember into a ClusterableModel or use a ForeignKey instead.')

    def test_parental_key_checks_related_name_is_not_plus(self):
        from django.core import checks
        from django.db import models
        from modelcluster.fields import ParentalKey

        class Instrument(models.Model):
            # Oops, related_name='+' is not allowed
            band = ParentalKey(Band, related_name='+', on_delete=models.CASCADE)

            class Meta:
                # Prevent Django from thinking this is in the database
                # This shouldn't affect the test
                abstract = True

        # Check for error
        errors = Instrument.check()
        self.assertEqual(1, len(errors))

        # Check the error itself
        error = errors[0]
        self.assertIsInstance(error, checks.Error)
        self.assertEqual(error.id, 'modelcluster.E002')
        self.assertEqual(error.obj, Instrument.band.field)
        self.assertEqual(error.msg, "related_name='+' is not allowed on ParentalKey fields")
        self.assertEqual(error.hint, "Either change it to a valid name or remove it")

    def test_parental_key_checks_target_is_resolved_as_class(self):
        from django.core import checks
        from django.db import models
        from modelcluster.fields import ParentalKey

        class Instrument(models.Model):
            banana = ParentalKey('Banana', on_delete=models.CASCADE)

            class Meta:
                # Prevent Django from thinking this is in the database
                # This shouldn't affect the test
                abstract = True

        # Check for error
        errors = Instrument.check()
        self.assertEqual(1, len(errors))

        # Check the error itself
        error = errors[0]
        self.assertIsInstance(error, checks.Error)
        self.assertEqual(error.id, 'fields.E300')
        self.assertEqual(error.obj, Instrument.banana.field)
        self.assertEqual(error.msg, "Field defines a relation with model 'Banana', which is either not installed, or is abstract.")


class GetAllChildRelationsTest(TestCase):
    def test_get_all_child_relations(self):
        self.assertEqual(
            set([rel.name for rel in get_all_child_relations(Restaurant)]),
            set(['tagged_items', 'reviews', 'menu_items'])
        )


class ParentalM2MTest(TestCase):
    def setUp(self):
        self.article = Article(title="Test Title")
        self.author_1 = Author.objects.create(name="Author 1")
        self.author_2 = Author.objects.create(name="Author 2")
        self.article.authors = [self.author_1, self.author_2]
        self.category_1 = Category.objects.create(name="Category 1")
        self.category_2 = Category.objects.create(name="Category 2")
        self.article.categories = [self.category_1, self.category_2]

    def test_uninitialised_m2m_relation(self):
        # Reading an m2m relation of a newly created object should return an empty queryset
        new_article = Article(title="Test title")
        self.assertEqual([], list(new_article.authors.all()))
        self.assertEqual(new_article.authors.count(), 0)

        # the manager should have a 'model' property pointing to the target model
        self.assertEqual(Author, new_article.authors.model)

    def test_parentalm2mfield(self):
        # Article should not exist in the database yet
        self.assertFalse(Article.objects.filter(title='Test Title').exists())

        # Test lookup on parental M2M relation
        self.assertEqual(
            ['Author 1', 'Author 2'],
            [author.name for author in self.article.authors.order_by('name')]
        )
        self.assertEqual(self.article.authors.count(), 2)

        # the manager should have a 'model' property pointing to the target model
        self.assertEqual(Author, self.article.authors.model)

        # Test adding to the relation
        author_3 = Author.objects.create(name="Author 3")
        self.article.authors.add(author_3)
        self.assertEqual(
            ['Author 1', 'Author 2', 'Author 3'],
            [author.name for author in self.article.authors.all().order_by('name')]
        )
        self.assertEqual(self.article.authors.count(), 3)

        # Test removing from the relation
        self.article.authors.remove(author_3)
        self.assertEqual(
            ['Author 1', 'Author 2'],
            [author.name for author in self.article.authors.order_by('name')]
        )
        self.assertEqual(self.article.authors.count(), 2)

        # Test clearing the relation
        self.article.authors.clear()
        self.assertEqual(
            [],
            [author.name for author in self.article.authors.order_by('name')]
        )
        self.assertEqual(self.article.authors.count(), 0)

        # Test the 'set' operation
        self.article.authors.set([self.author_2])
        self.assertEqual(self.article.authors.count(), 1)
        self.assertEqual(
            ['Author 2'],
            [author.name for author in self.article.authors.order_by('name')]
        )

        # Test saving to / restoring from DB
        self.article.authors = [self.author_1, self.author_2]
        self.article.save()
        self.article = Article.objects.get(title="Test Title")
        self.assertEqual(
            ['Author 1', 'Author 2'],
            [author.name for author in self.article.authors.order_by('name')]
        )
        self.assertEqual(self.article.authors.count(), 2)

    def test_constructor(self):
        # Test passing values for M2M relations as kwargs to the constructor
        article2 = Article(
            title="Test article 2",
            authors=[self.author_1],
            categories=[self.category_2],
        )
        self.assertEqual(
            ['Author 1'],
            [author.name for author in article2.authors.order_by('name')]
        )
        self.assertEqual(article2.authors.count(), 1)

    def test_ordering(self):
        # our fake querysets should respect the ordering defined on the target model
        bela_bartok = Author.objects.create(name='Bela Bartok')
        graham_greene = Author.objects.create(name='Graham Greene')
        janis_joplin = Author.objects.create(name='Janis Joplin')
        simon_sharma = Author.objects.create(name='Simon Sharma')
        william_wordsworth = Author.objects.create(name='William Wordsworth')

        article3 = Article(title="Test article 3")
        article3.authors = [
            janis_joplin, william_wordsworth, bela_bartok, simon_sharma, graham_greene
        ]
        self.assertEqual(
            list(article3.authors.all()),
            [bela_bartok, graham_greene, janis_joplin, simon_sharma, william_wordsworth]
        )

    def test_save_m2m_with_update_fields(self):
        self.article.save()

        # modify both relations, but only commit the change to authors
        self.article.authors.clear()
        self.article.categories.clear()
        self.article.title = 'Updated title'
        self.article.save(update_fields=['title', 'authors'])

        self.updated_article = Article.objects.get(pk=self.article.pk)
        self.assertEqual(self.updated_article.title, 'Updated title')
        self.assertEqual(self.updated_article.authors.count(), 0)
        self.assertEqual(self.updated_article.categories.count(), 2)

    def test_reverse_m2m_field(self):
        # article is unsaved, so should not be returned by the reverse relation on author
        self.assertEqual(self.author_1.articles_by_author.count(), 0)

        self.article.save()
        # should now be able to look up on the reverse relation
        self.assertEqual(self.author_1.articles_by_author.count(), 1)
        self.assertEqual(self.author_1.articles_by_author.get(), self.article)

        article_2 = Article(title="Test Title 2")
        article_2.authors = [self.author_1]
        article_2.save()
        self.assertEqual(self.author_1.articles_by_author.all().count(), 2)
        self.assertEqual(
            list(self.author_1.articles_by_author.order_by('title').values_list('title', flat=True)),
            ['Test Title', 'Test Title 2']
        )

    def test_value_from_object(self):
        authors_field = Article._meta.get_field('authors')
        self.assertEqual(
            set(authors_field.value_from_object(self.article)),
            set([self.author_1, self.author_2])
        )
        self.article.save()
        self.assertEqual(
            set(authors_field.value_from_object(self.article)),
            set([self.author_1, self.author_2])
        )


class PrefetchRelatedTest(TestCase):
    def test_fakequeryset_prefetch_related(self):
        person1 = Person.objects.create(name='Joe')
        person2 = Person.objects.create(name='Mary')

        # Set main_room for each house before creating the next one for
        # databases where supports_nullable_unique_constraints is False.

        house1 = House.objects.create(name='House 1', address='123 Main St', owner=person1)
        room1_1 = Room.objects.create(name='Dining room')
        room1_2 = Room.objects.create(name='Lounge')
        room1_3 = Room.objects.create(name='Kitchen')
        house1.main_room = room1_1
        house1.save()

        house2 = House(name='House 2', address='45 Side St', owner=person1)
        room2_1 = Room.objects.create(name='Eating room')
        room2_2 = Room.objects.create(name='TV Room')
        room2_3 = Room.objects.create(name='Bathroom')
        house2.main_room = room2_1

        person1.houses = itertools.chain(House.objects.all(), [house2])

        houses = person1.houses.all()

        with self.assertNumQueries(1):
            qs = person1.houses.prefetch_related('main_room')

        with self.assertNumQueries(0):
            main_rooms = [ house.main_room for house in person1.houses.all() ]
            self.assertEqual(len(main_rooms), 2)
