/* An auto-complete module for select and input elements that can pull in
 * a list of terms from an API endpoint (provided using data-module-source).
 *
 * source   - A url pointing to an API autocomplete endpoint.
 * interval - The interval between requests in milliseconds (default: 300).
 * items    - The max number of items to display (default: 10)
 * tags     - Boolean attribute if true will create a tag input.
 * key      - A string of the key you want to be the form value to end up on
 *            from the ajax returned results
 * label    - A string of the label you want to appear within the dropdown for
 *            returned results
 * tokensep - A string that contains characters which will be interpreted
 *            as separators for tags when typed or pasted (default ",").
 * Examples
 *
 *   // <input name="tags" data-module="autocomplete" data-module-source="http://" />
 *
 */
jQuery(document).ready(function () {
  ckan.module('qdes_autocomplete', function (jQuery) {
    return {
      /* Options for the module */
      options: {
        tags: false,
        createtags: true,
        key: false,
        label: false,
        title: false,
        items: 10,
        source: null,
        tokensep: ',',
        interval: 300,
        dropdownClass: '',
        containerClass: '',
        allowClear: true,
        createSearchChoice: false,
        id: '',
        type: '',
        vocabularyServiceName: '',
        minimumInputLength: 0
      },

      /* Sets up the module, binding methods, creating elements etc. Called
       * internally by ckan.module.initialize();
       *
       * Returns nothing.
       */
      initialize: function () {
        jQuery.proxyAll(this, /_on/, /format/);
        this.setupAutoComplete();
      },

      /* Sets up the auto complete plugin.
       *
       * Returns nothing.
       */
      setupAutoComplete: function () {
        var settings = {
          width: 'resolve',
          formatResult: this.formatResult,
          formatNoMatches: this.formatNoMatches,
          formatInputTooShort: this.formatInputTooShort,
          dropdownCssClass: this.options.dropdownClass,
          containerCssClass: this.options.containerClass,
          tokenSeparators: this.options.tokensep.split(''),
          allowClear: this.options.allowClear,
          minimumInputLength: this.options.minimumInputLength
        };

        // If source is set for API, replace the id placeholder with id passed in
        if (this.options.source && this.options.id) {
          this.options.source = this.options.source.replace('<id>', this.options.id);
        }

        // Different keys are required depending on whether the select is
        // tags or generic completion.
        if (!this.el.is('select')) {
          if (this.options.tags) {
            settings.tags = this._onQuery;

            // Disable creating new tags
            if (!this.options.createtags) {
              settings.createSearchChoice = function (params) {
                return undefined;
              }
            }
          } else {
            settings.query = this._onQuery;
            // If there is no match from search results, allow user to create new choice option
            if (this.options.createSearchChoice) {
              settings.createSearchChoice = this.formatTerm;
            }
            else {
              // Search needs to find a match to be selected
              settings.createSearchChoice = function (params) {
                return undefined;
              }
            }
          }
          settings.initSelection = this.formatInitialValue;
        }
        else {
          if (/MSIE (\d+\.\d+);/.test(navigator.userAgent)) {
            var ieversion = new Number(RegExp.$1);
            if (ieversion <= 7) { return }
          }
        }

        var select2 = this.el.select2(settings).data('select2');

        if (this.options.tags && select2 && select2.search) {
          // find the "fake" input created by select2 and add the keypress event.
          // This is not part of the plugins API and so may break at any time.
          select2.search.on('keydown', this._onKeydown);
        }

        // This prevents Internet Explorer from causing a window.onbeforeunload
        // even from firing unnecessarily
        $('.select2-choice', select2.container).on('click', function () {
          return false;
        });

        this.el.on('select2-selecting', function (e) {
            $('.tooltip').remove();
        });

        this._select2 = select2;
      },

      /* Looks up the completions for the current search term and passes them
       * into the provided callback function.
       *
       * The results are formatted for use in the select2 autocomplete plugin.
       *
       * string - The term to search for.
       * fn     - A callback function.
       *
       * Examples
       *
       *   module.getCompletions('cake', function (results) {
       *     results === {results: []}
       *   });
       *
       * Returns a jqXHR promise.
       */
      getCompletions: function (string, fn) {
        var parts = this.options.source.split('?');
        var end = parts.pop();
        var source = parts.join('?') + encodeURIComponent(string) + end;
        if (this.options.id.length > 0) {
          source += "&dataset_id=" + this.options.id;
        }
        if (this.options.type.length > 0) {
          source += "&dataset_type=" + this.options.type;
        }
        if (source.indexOf('{vocabularyServiceName}') >= 0 && this.options.vocabularyServiceName.length > 0) {
          source = source.replace("{vocabularyServiceName}", this.options.vocabularyServiceName);
        }
        var client = this.sandbox.client;
        var parseCompletions = this.parseCompletions;
        var options = {
          format: function (data) {
            var completion_options = jQuery.extend(options, { objects: true });
            return {
              results: parseCompletions(data, completion_options)
            }
          },
          key: this.options.key,
          label: this.options.label,
          title: this.options.title
        };

        return client.getCompletions(source, options, fn);
      },

    /* Copied from ckan/public/base/javascript/client.js and modified to add title property to object returned 
     * Takes a JSON response from an auto complete endpoint and normalises
     * the data into an array of strings. This also will remove duplicates
     * from the results (this is case insensitive).
     *
     * data    - The parsed JSON response from the server.
     * options - An object of options for the method.
     *           objects: If true returns an object of results.
     *
     * Examples
     *
     *   jQuery.getJSON(tagCompletionUrl, function (data) {
     *     var parsed = client.parseCompletions(data);
     *   });
     *
     * Returns the parsed object.
     */
      parseCompletions: function (data, options) {
        if (typeof data === 'string') {
          // Package completions are returned as a crazy string. So we handle
          // them separately.
          return this.parsePackageCompletions(data, options);
        }

        var map = {};
        // If given a 'result' array then convert it into a Result dict inside a Result dict.
        // new syntax (not used until all browsers support arrow notation):
        //data = data.result ? { 'ResultSet': { 'Result': data.result.map(x => ({'Name': x})) } } : data;
        // compatible syntax:
        data = data.result ? { 'ResultSet': { 'Result': data.result.map(function (val) { return { 'Name': val } }) } } : data;
        // If given a Result dict inside a ResultSet dict then use the Result dict.
        var raw = jQuery.isArray(data) ? data : data.ResultSet && data.ResultSet.Result || {};

        var items = jQuery.map(raw, function (item) {
          var key = typeof options.key != 'undefined' ? item[options.key] : false;
          var label = typeof options.label != 'undefined' ? item[options.label] : false;
          var title = typeof options.title != 'undefined' ? item[options.title] : false;

          item = typeof item === 'string' ? item : item.name || item.Name || item.Format || '';
          item = jQuery.trim(item);

          key = key ? key : item;
          label = label ? label : item;
          title = title ? title : '';

          var lowercased = item.toLowerCase();
          var returnObject = options && options.objects === true;

          if (lowercased && !map[lowercased]) {
            map[lowercased] = 1;
            return returnObject ? { id: key, text: label, title: title } : item;
          }

          return null;
        });

        // Remove duplicates.
        items = jQuery.grep(items, function (item) { return item !== null; });

        return items;
      },

      /* Looks up the completions for the provided text but also provides a few
       * optimisations. If there is no search term it will automatically set
       * an empty array. Ajax requests will also be debounced to ensure that
       * the server is not overloaded.
       *
       * string - The term to search for.
       * fn     - A callback function.
       *
       * Returns nothing.
       */
      lookup: function (string, fn) {
        var module = this;

        // Cache the last searched term otherwise we'll end up searching for
        // old data.
        this._lastTerm = string;

        // Kills previous timeout
        clearTimeout(this._debounced);

        // OK, wipe the dropdown before we start ajaxing the completions
        fn({ results: [] });

        if (string) {
          // Set a timer to prevent the search lookup occurring too often.
          this._debounced = setTimeout(function () {
            var term = module._lastTerm;

            // Cancel the previous request if it hasn't yet completed.
            if (module._last && typeof module._last.abort == 'function') {
              module._last.abort();
            }

            module._last = module.getCompletions(term, fn);
          }, this.options.interval);

          // This forces the ajax throbber to appear, because we've called the
          // callback already and that hides the throbber
          $('.select2-search input', this._select2.dropdown).addClass('select2-active');
        }
      },

      /* Formatter for the select2 plugin that returns a string for use in the
       * results list with the current term emboldened.
       *
       * state     - The current object that is being rendered.
       * container - The element the content will be added to (added in 3.0)
       * query     - The query object (added in select2 3.0).
       *
       *
       * Returns a text string.
       */
      formatResult: function (state, container, query, escapeMarkup) {
        var term = this._lastTerm || (query ? query.term : null) || null; // same as query.term

        if (container) {
          // Append the select id to the element for styling.
          container.attr('data-value', state.id);
          // Add container title attribute either from select element or state object property
          if (state.element && state.element[0]) {
            container.prop('title', state.element[0].title);
          }
          else if (state.title) {
            container.prop('title', state.title);
          }
          container.on("mouseover", this._initialiseTooltip.bind(this));
        }

        var result = [];
        $(state.text.split(term)).each(function () {
          result.push(escapeMarkup ? escapeMarkup(this) : this);
        });

        return result.join(term && (escapeMarkup ? escapeMarkup(term) : term).bold());
      },

      /* Formatter for the select2 plugin that returns a string used when
       * the filter has no matches.
       *
       * Returns a text string.
       */
      formatNoMatches: function (term) {
        return !term ? this._('Start typing…') : this._('No matches found');
      },

      /* Formatter used by the select2 plugin that returns a string when the
       * input is too short.
       *
       * Returns a string.
       */
      formatInputTooShort: function (term, min) {
        return this.ngettext(
          'Input is too short, must be at least one character',
          'Input is too short, must be at least %(num)d characters',
          min
        );
      },

      /* Takes a string and converts it into an object used by the select2 plugin.
       *
       * term - The term to convert.
       *
       * Returns an object for use in select2.
       */
      formatTerm: function (term) {
        term = jQuery.trim(term || '');

        // Need to replace comma with a unicode character to trick the plugin
        // as it won't split this into multiple items.
        return { id: term.replace(/,/g, '\u002C'), text: term };
      },

      /* Callback function that parses the initial field value.
       *
       * element  - The initialized input element wrapped in jQuery.
       * callback - A callback to run once the formatting is complete.
       *
       * Returns a term object or an array depending on the type.
       */
      formatInitialValue: function (element, callback) {
        var value = jQuery.trim(element.val() || '');
        var formatted;

        if (this.options.tags) {
          formatted = jQuery.map(value.split(","), this.formatTerm);
        } else if (this.options.source) {
          // If a API source is used, check if the value is a json object to preselect the initial value
          try {
            formatted = JSON.parse(value);
            // Set the element value to the object id so on form submit the id value is used instead of the JSON object
            element[0].value = formatted.id;
          } catch (e) {
            formatted = this.formatTerm(value);
          }
        } else {
          formatted = this.formatTerm(value);
        }

        // Select2 v3.0 supports a callback for async calls.
        if (typeof callback === 'function') {
          callback(formatted);
        }

        return formatted;
      },

      /* Callback triggered when the select2 plugin needs to make a request.
       *
       * Returns nothing.
       */
      _onQuery: function (options) {
        if (options) {
          this.lookup(options.term, options.callback);
        }
      },

      /* Called when a key is pressed.  If the key is a comma we block it and
       * then simulate pressing return.
       *
       * Returns nothing.
       */
      _onKeydown: function (event) {
        if (typeof event.key !== 'undefined' ? event.key === ',' : event.which === 188) {
          event.preventDefault();
          setTimeout(function () {
            var e = jQuery.Event("keydown", { which: 13 });
            jQuery(event.target).trigger(e);
          }, 10);
        }
      },

      /* Initialise the elements bootstrap tooltip
       *
       * Returns nothing.
       */            
      _initialiseTooltip : function (event) {
        // Only initialise tooltip if it has not been initialised yet
        if(jQuery(event.target).data('bs.tooltip') === undefined) {
          jQuery(event.target).tooltip({
            "placement": "auto",
            "delay": {"show": 500, "hide": 100},
            "container": 'body'
          });
          setTimeout(this._showTooltip, 500, event.target);
        }
      },

      /* Show the tooltip after its been initialised only if the mouse is still hovering over the element
       *
       * Returns nothing.
       */
      _showTooltip : function (container) {
        if(jQuery(container).is(":hover")) {
          jQuery(container).tooltip('show');
        }
      }
    };
  });
});
