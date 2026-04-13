from django.contrib import admin
from django import forms
from django.utils.html import format_html
from django.utils import timezone
from .models import Faculty, Department, Student, Course, Lecture, Enrollment, Assessment, Grade

# ========== HELPER FUNCTION ==========
def get_letter_grade(score):
    if score is None:
        return None
    if score >= 90: return 'A'
    elif score >= 85: return 'A-'
    elif score >= 80: return 'B+'
    elif score >= 75: return 'B'
    elif score >= 70: return 'B-'
    elif score >= 65: return 'C+'
    elif score >= 60: return 'C'
    elif score >= 55: return 'C-'
    elif score >= 50: return 'D'
    else: return 'F'

# ========== GRADE FORM ==========
class GradeForm(forms.ModelForm):
    override_reason = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 2, 'style': 'width: 100%;'}),
        label="Override Reason"
    )
    
    class Meta:
        model = Grade
        fields = ['studentid', 'assessmentid', 'score', 'override_reason']
    
    def clean_score(self):
        score = self.cleaned_data.get('score')
        if score is not None and (score < 0 or score > 100):
            raise forms.ValidationError("Grade must be between 0 and 100")
        return score
    
    def clean(self):
        cleaned_data = super().clean()
        score = cleaned_data.get('score')
        override_reason = cleaned_data.get('override_reason')
        assessment = cleaned_data.get('assessmentid')
        
        if assessment and score is not None:
            all_grades = Grade.objects.filter(
                assessmentid=assessment
            ).exclude(gradeid=self.instance.gradeid).values_list('score', flat=True)
            all_grades = [g for g in all_grades if g is not None]
            
            if all_grades:
                average = sum(all_grades) / len(all_grades)
                difference = abs(score - average)
                
                if difference > 25:
                    self.instance.was_flagged = True
                    self.instance.class_average = average
                    
                    if not override_reason:
                        raise forms.ValidationError(
                            f"⚠️ AI WARNING: This grade ({score}) is very different "
                            f"from class average ({average:.1f}). Please provide a reason."
                        )
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if instance.score is not None:
            instance.lettergrade = get_letter_grade(instance.score)
        if not instance.submissiondate:
            instance.submissiondate = timezone.now()
        if commit:
            instance.save()
        return instance

# ========== GRADE ADMIN ==========
class GradeAdmin(admin.ModelAdmin):
    form = GradeForm
    list_display = ('student_name', 'assessment_name', 'score', 'lettergrade', 'status_indicator', 'override_reason_preview', 'submission_date')
    list_filter = ('assessmentid', 'studentid')
    search_fields = ('studentid__firstname', 'studentid__lastname', 'assessmentid__assessmentname')
    
    def student_name(self, obj):
        return f"{obj.studentid.firstname} {obj.studentid.lastname}"
    student_name.short_description = 'Student'
    
    def assessment_name(self, obj):
        return obj.assessmentid.assessmentname
    assessment_name.short_description = 'Assessment'
    
    def submission_date(self, obj):
        if obj.submissiondate:
            return obj.submissiondate.strftime('%Y-%m-%d %H:%M')
        return '-'
    submission_date.short_description = 'Date Submitted'
    
    def status_indicator(self, obj):
        if hasattr(obj, 'was_flagged') and obj.was_flagged:
            if obj.override_reason:
                return format_html('<span style="color: orange;">⚠️ Overridden</span>')
            else:
                return format_html('<span style="color: red;">⚠️ Flagged</span>')
        return format_html('<span style="color: green;">✓ Normal</span>')
    status_indicator.short_description = 'Status'
    
    def override_reason_preview(self, obj):
        if obj.override_reason:
            preview = obj.override_reason[:50] + '...' if len(obj.override_reason) > 50 else obj.override_reason
            return format_html('<span title="{}">💬 {}</span>', obj.override_reason, preview)
        return '-'
    override_reason_preview.short_description = 'Override Reason'

# ========== LECTURER ADMIN ==========
class LectureAdmin(admin.ModelAdmin):
    list_display = ('lecturer_name', 'email', 'departmentid')
    search_fields = ('firstname', 'lastname', 'email')
    
    def lecturer_name(self, obj):
        return f"{obj.firstname} {obj.lastname}"
    lecturer_name.short_description = 'Lecturer'

# ========== REGISTER MODELS ==========
admin.site.register(Faculty)
admin.site.register(Department)
admin.site.register(Student)
admin.site.register(Course)
admin.site.register(Lecture, LectureAdmin)
admin.site.register(Enrollment)
admin.site.register(Assessment)

try:
    admin.site.unregister(Grade)
except:
    pass
admin.site.register(Grade, GradeAdmin)
from .models import UserProfile  # Add this at the top with other imports

# Add this at the bottom of the file
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role')
    list_filter = ('role',)
    search_fields = ('user__username', 'user__email')

admin.site.register(UserProfile, UserProfileAdmin)