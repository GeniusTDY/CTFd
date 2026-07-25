CTFd.plugin.run((_CTFd) => {
    const $ = _CTFd.lib.$;

    // Use CTFd core's global _() function (powered by Flask-Babel translations)
    const _t = (key, params) => {
        let translated = _(key);
        if (params) {
            Object.keys(params).forEach(k => {
                translated = translated.replace('%(' + k + ')s', params[k]);
            });
        }
        return translated;
    };

    let questionCount = 1;

    function initCreateForm() {
        // Add question button
        $('#add-question').click(function () {
            questionCount++;

            const questionHtml = `
                <div class="question-item border p-3 mb-3" data-question="${questionCount}">
                    <div class="form-group">
                        <label class="question-label">${_t('Question %(num)s', {num: questionCount})}</label>
                        <textarea class="form-control question-text" name="question_${questionCount}" rows="3" placeholder="${_t('Enter question text')}" required></textarea>
                    </div>
                    <div class="form-group">
                        <label class="flag-label">${_t('Flag %(num)s', {num: questionCount})}</label>
                        <input type="text" class="form-control question-flag" name="flag_${questionCount}" placeholder="${_t('Enter flag')}" required>
                    </div>
                    <div class="form-group">
                        <label>${_t('Points')}</label>
                        <input type="number" class="form-control question-points" name="points_${questionCount}" value="100" min="1" required>
                    </div>
                </div>
            `;

            $('#questions-container').append(questionHtml);

            // Show remove button if more than 1 question
            if (questionCount > 1) {
                $('#remove-question').show();
            }
        });

        // Remove question button
        $('#remove-question').click(function () {
            if (questionCount > 1) {
                $('.question-item').last().remove();
                questionCount--;

                // Hide remove button if only 1 question left
                if (questionCount <= 1) {
                    $('#remove-question').hide();
                }
            }
        });

        // Ensure challenge type is set correctly
        $('#chaltype').val('subquestionchallenge');

        // The form submission is completely overridden by this script.
        const form = $('form[action="/admin/challenges/new"], form[x-action="create_challenge"]');

        if (form.data('multi-question-bound')) {
            console.log("Multi Question Challenge create script already bound, skipping.");
            return;
        }
        form.data('multi-question-bound', true);

        // Detach all existing submit handlers to prevent duplicate submissions
        form.off('submit');

        form.on('submit', function (e) {
            e.preventDefault();
            e.stopImmediatePropagation();

            const submitButton = $('.create-challenge-submit');
            submitButton.prop('disabled', true);

            // Validate required fields
            const name = $('input[name="name"]').val();
            const category = $('input[name="category"]').val();

            if (!name || !category) {
                alert(_('Please fill out the challenge name and category'));
                submitButton.prop('disabled', false);
                return;
            }

            // Check if we have at least one question
            const question1 = $('textarea[name="question_1"]').val();
            const flag1 = $('input[name="flag_1"]').val();

            if (!question1 || !flag1) {
                alert(_('Please fill out at least one question and its corresponding flag'));
                submitButton.prop('disabled', false);
                return;
            }

            // Collect all form data into a JSON object
            const data = {};
            const formData = new FormData(this);
            for (const [key, value] of formData.entries()) {
                data[key] = value;
            }

            // Ensure the challenge type is set correctly
            data['type'] = 'subquestionchallenge';

            // Use CTFd.fetch to submit to the correct API endpoint
            _CTFd.fetch('/api/v1/challenges', {
                method: 'POST',
                body: JSON.stringify(data),
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                }
            })
                .then(response => {
                    if (response.ok) {
                        return response.json();
                    } else {
                        return response.json().then(err => { throw err; });
                    }
                })
                .then(response => {
                    if (response.success) {
                        window.location.href = '/admin/challenges';
                    } else {
                        console.error('Create failed:', response);
                        let error_message = _('Failed to create challenge. Please check all fields are filled correctly.');
                        if (response.errors) {
                            error_message = Object.values(response.errors).join('\n');
                        }
                        alert(error_message);
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert(_('An error occurred while creating the challenge'));
                })
                .finally(() => {
                    submitButton.prop('disabled', false);
                });
        });

        // We no longer need a separate click handler for the button
        $('.create-challenge-submit').off('click');

        console.log("Multi Question Challenge create script loaded and form submission overridden.");
    }

    initCreateForm();
});
