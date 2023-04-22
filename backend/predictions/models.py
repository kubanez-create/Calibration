from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Prediction(models.Model):
    """Predictions model."""
    user_id = models.ForeignKey(User, on_delete=models.CASCADE,
                                related_name='predictions')
    date = models.DateTimeField('Creation time', auto_now_add=True)
    description = models.CharField('Description', max_length=500)
    category = models.CharField('Category', max_length=50)
    unit_of_measure = models.CharField('Unit of measure', max_length=30)
    pred_low_50_conf = models.FloatField(
        'Lower bound on prediction with 50% confidence')
    pred_high_50_conf = models.FloatField(
        'Upper bound on prediction with 50% confidence')
    pred_low_90_conf = models.FloatField(
        'Lower bound on prediction with 90% confidence')
    pred_high_90_conf = models.FloatField(
        'Upper bound on prediction with 90% confidence')
    actual = models.FloatField(
        'Actual outcome of a prediction')
