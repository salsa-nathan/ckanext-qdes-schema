(function ($) {
    $(document).ready(function () {
        /**
         * This module is a modified version of core confirm action,
         * the modal can handle a new modal when cancel button is clicked.
         */
        ckan.module('publish-confirm-action', function ($) {
            return {
                /* An object of module options */
                options: {
                    cancel: false,
                    content: '',
                    contentCancel: '',
                    withData: '',
                    template: [
                        '<div class="modal fade">',
                        '<div class="modal-dialog">',
                        '<div class="modal-content">',
                        '<div class="modal-header">',
                        '<button type="button" class="close" data-dismiss="modal">×</button>',
                        '<h3 class="modal-title"></h3>',
                        '</div>',
                        '<div class="modal-body"></div>',
                        '<div class="modal-footer">',
                        '<button class="btn btn-default btn-cancel"></button>',
                        '<button class="btn btn-primary"></button>',
                        '</div>',
                        '</div>',
                        '</div>',
                        '</div>'
                    ].join('\n')
                },

                /* Sets up the event listeners for the object. Called internally by
                 * module.createInstance().
                 *
                 * Returns nothing.
                 */
                initialize: function () {
                    $.proxyAll(this, /_on/);
                    this.el.on('click', this._onClick);
                },
                confirm: function () {
                    this.sandbox.body.append(this.createModal());
                    this.modal.on('hidden.bs.modal', this._onModalHidden);
                    this.modal.on('show.bs.modal', this._onModalShow);
                    this.modal.modal('show');


                    // Center the modal in the middle of the screen.
                    this.modal.css({
                        'margin-top': this.modal.height() * -0.5,
                        'top': '50%'
                    });
                },
                performAction: function () {
                    // create a form and submit it to confirm the deletion
                    var $form = $('<form/>', {
                        action: this.el.attr('href'),
                        method: 'POST'
                    });

                    // use parent to el form if data-module-with-data == true
                    if (this.options.withData) {
                        var $form = this.el.closest('form');

                        // Send the button value.
                        $form.append('<input type="hidden" name="' + this.el.attr('name') + '" value="' + this.el.attr('value') + '">');
                    }

                    $form.appendTo('body').submit();
                },
                /* Creates the modal dialog, attaches event listeners.
                 *
                 * Returns the newly created element.
                 */
                createModal: function () {
                    if (!this.modal) {
                        var element = this.modal = $(this.options.template);
                        var content = this.options.content;
                        element.on('click', '.btn-primary', this._onConfirmSuccess);
                        element.on('click', '.btn-cancel', this._onPublishCancel);
                        element.find('.modal-title').text(this._('Please Confirm Action'));
                        element.find('.modal-body').text(content);
                        element.find('.btn-primary').text(this._('Yes'));
                        element.find('.btn-cancel').text(this._('No'));
                        element.modal({show: false});
                    }

                    return this.modal;
                },
                /* Event handler that displays the confirm dialog */
                _onClick: function (event) {
                    event.preventDefault();
                    this.confirm();
                },
                /* Event handler for the success event */
                _onConfirmSuccess: function (event) {
                    if (this.options.cancel) {
                        this.options.cancel = false;
                    } else {
                        this.performAction();
                    }
                },
                _onPublishCancel: function (event) {
                    this.options.cancel = true;
                    this.modal.modal('hide');
                },
                _onConfirmCancel: function (event) {
                    this.modal.modal('hide');
                },
                _onModalHidden: function (event) {
                    if (this.options.cancel) {
                        this.confirm();
                    } else {
                        this.modal.find('.btn-cancel').show();
                    }
                },
                _onModalShow: function (event) {
                    if (this.options.cancel) {
                        var element = this.modal;
                        element.on('click', '.btn-primary', this._onConfirmCancel);
                        element.find('.btn-cancel').hide();
                        element.find('.modal-body').text(this.options.contentCancel);
                        element.find('.btn-primary').text(this._('Confirm'));

                        // Disable publish button.
                        var $validatePublishEl = $('.validate-publish');
                        var $publishBtnEl = $validatePublishEl.find('.publish');
                        $publishBtnEl.attr('disabled', true);
                        $validatePublishEl.attr('data-valid', 0);
                    }
                }
            };
        });
    });

    $(document).ready(function () {
        var $validatePublishEl = $('.validate-publish');
        var $resourcesEl = $validatePublishEl.find('.resources');
        var $schemaEl = $validatePublishEl.find('#schema');
        var $validateBtnEl = $validatePublishEl.find('.validate');
        var $publishBtnEl = $validatePublishEl.find('.publish');
        var $infoEl = $validatePublishEl.find('.alert.alert-info');
        var isPublic = $validatePublishEl.attr('data-public') === "1";
        var isOfficialPublic = $validatePublishEl.attr('data-official-public') === "1";
        var isQspatialHarvested = $validatePublishEl.attr('data-qspatial-harvested') === "1";
        var isSeries = $validatePublishEl.attr('data-series') === "1";
        var isSeriesParent = $validatePublishEl.attr('data-series-parent') === "1";
        var isValid = $validatePublishEl.attr('data-valid') === "1" && isPublic && isOfficialPublic;
        var isOpenDataSelected = $schemaEl.val() !== 'dataqld_dataset';
        var resourceChecked = function () {
            var checked = false
            $resourcesEl.each(function () {
                if ($(this).prop('checked')) {
                    checked = true;
                }
            });

            return checked;
        }
        var showInfoText = function (isPublic, isOfficialPublic) {
            if ($schemaEl.val() !== 'none') {
                if (!isPublic) {
                    $infoEl.html('The dataset\'s visibility is currently set to "Private" and cannot be published. Please change the visibility setting to "Public before publishing."');
                    $infoEl.show();

                    return true;
                } else if (!isOfficialPublic) {
                    $infoEl.html('The dataset\'s classification and access restriction does not permit publishing. Only dataset’s with a classification of "OFFICIAL-PUBLIC" can be published.');
                    $infoEl.show();

                    return true;
                } else if (isOpenDataSelected && isQspatialHarvested && isSeries) {
                    if (isSeriesParent) {
                        $infoEl.html('This series/collection distribution was originally sourced from QSpatial. Please publish any changes to QSpatial. The Data.QLD record will be automatically updated via QSpatial.');
                    } else {
                        $infoEl.html('This distribution is part of a series/collection that was originally sourced from QSpatial. Please publish any changes to QSpatial. The Data.QLD record will be automatically updated via QSpatial.');
                    }

                    $infoEl.show();

                    return true;
                }
            } else {
                $infoEl.hide();
            }

            return false;
        }
        var toggleBtnOnOff = function (isPublic, isOfficialPublic, checkValid = false) {
            if ($schemaEl.val() !== 'none' && resourceChecked()) {
                // Enable button.
                $validateBtnEl.attr('disabled', false);
            } else {
                // Disable buttons.
                $validateBtnEl.attr('disabled', true);
                $publishBtnEl.attr('disabled', true);
            }

            if (checkValid && isValid) {
                // Enable both buttons if valid.
                $validateBtnEl.attr('disabled', false);
                $publishBtnEl.attr('disabled', false);
            }

            if (!checkValid && isValid) {
                // If this already valid, and the checkbox value changed,
                // user need to re-validate it again, just in case the selected resource
                // is not valid.
                if (isValid) {
                    isValid = false;
                    $validatePublishEl.attr('data-valid', 0);
                    $publishBtnEl.attr('disabled', true);
                    $validatePublishEl.find('.alert-success').remove();
                }
            }

            if (!isPublic || !isOfficialPublic || (isOpenDataSelected && isQspatialHarvested && isSeries)) {
                // Disable buttons.
                $validateBtnEl.attr('disabled', true);
                $publishBtnEl.attr('disabled', true);
            }
        }

        // Listen on checkbox change event.
        $resourcesEl.on('change', function () {
            toggleBtnOnOff(isPublic, isOfficialPublic);
        });

        // Listen to dropdown change event.
        $schemaEl.on('change', function () {
            showInfoText(isPublic, isOfficialPublic);
            toggleBtnOnOff(isPublic, isOfficialPublic);
        });

        // Init.
        toggleBtnOnOff(isPublic, isOfficialPublic, true);

        // Prevent resubmit on refresh,
        // this is not ideal but since the error/success msg
        // is on different place than the flash, then this workaround needed.
        if (window.history.replaceState) {
            window.history.replaceState(null, null, window.location.href);
        }
    });

    $(document).ready(function () {
        var $unPublishEl = $('.unpublish-wrapper');
        var $resourceEl = $unPublishEl.find('#unpublish-resource');
        var $destinationEl = $unPublishEl.find('#schema-unpublish');
        var $unPublishBtnEl = $unPublishEl.find('.unpublish');
        var toggleBtnOnOff = function () {
            if ($resourceEl.val() !== 'none' && $destinationEl.val() !== 'none') {
                $unPublishBtnEl.attr('disabled', false);
            } else {
                $unPublishBtnEl.attr('disabled', true);
            }
        }

        $resourceEl.on('change', function () {
            toggleBtnOnOff();
        });

        $destinationEl.on('change', function () {
            toggleBtnOnOff();
        });

        // Init.
        toggleBtnOnOff();
    });
})(jQuery)
