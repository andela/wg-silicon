# -*- coding: utf-8 -*-

# This file is part of wger Workout Manager.
#
# wger Workout Manager is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# wger Workout Manager is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License

from rest_framework import serializers
from wger.exercises.models import (
    Muscle,
    Exercise,
    ExerciseImage,
    ExerciseCategory,
    Equipment,
    ExerciseComment
)


class ExerciseSerializer(serializers.ModelSerializer):
    '''
    Exercise serializer
    '''
    class Meta:
        model = Exercise


class EquipmentSerializer(serializers.ModelSerializer):
    '''
    Equipment serializer
    '''
    class Meta:
        model = Equipment


class ExerciseInfoSerializer(serializers.ModelSerializer):
    '''
    Exercise info serialiser
    '''

    exercise_images_list = serializers.StringRelatedField(
        source='get_exercise_image', many=True
    )
    description = serializers.ReadOnlyField(source='description_clean')
    muscles = serializers.StringRelatedField(many=True)
    language = serializers.StringRelatedField(many=False)
    category = serializers.StringRelatedField()
    equipment = serializers.StringRelatedField(many=True)
    muscles_secondary = serializers.StringRelatedField(many=True)
    license = serializers.StringRelatedField()

    class Meta:
        model = Exercise
        fields = ('id', 'name', 'name_original', 'category', 'equipment',
                  'description', 'muscles', 'muscles_secondary',
                  'exercise_images_list', 'language', 'license',
                  'license_author', 'creation_date')


class ExerciseCategorySerializer(serializers.ModelSerializer):
    '''
    ExerciseCategory serializer
    '''
    class Meta:
        model = ExerciseCategory


class ExerciseImageSerializer(serializers.ModelSerializer):
    '''
    ExerciseImage serializer
    '''
    class Meta:
        model = ExerciseImage


class ExerciseCommentSerializer(serializers.ModelSerializer):
    '''
    ExerciseComment serializer
    '''
    class Meta:
        model = ExerciseComment


class MuscleSerializer(serializers.ModelSerializer):
    '''
    Muscle serializer
    '''
    class Meta:
        model = Muscle
