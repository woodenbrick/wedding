YAHOO.util.Event.addListener(window, "load", function() {
    EnhanceFromMarkup_update = new function() {
        YAHOO.widget.DataTable.prototype.saveCellEditor = function() {
            // ++++ this is the inner function to handle the several possible failure conditions
            var onFailure = function (msg) {
                alert(msg);
            };
            
            var myBuildUrl = function(datatable,record) {
                var url = '';
                var cols = datatable.getColumnSet().keys;
                for (var i = 0; i < cols.length; i++) {
                    if (cols[i].isPrimaryKey) {
                        url += '&' + cols[i].key + '=' + encodeURIComponent(record.getData(cols[i].key));
                    }
                }
                return url;
            };

           // +++ this comes from the original except for the part I cut to place in the function above.
            if (this._oCellEditor.isActive) {
                var newData = this._oCellEditor.value;
                // Copy the data to pass to the event
                var oldData = YAHOO.widget.DataTable._cloneObject(this._oCellEditor.record.getData(this._oCellEditor.column.key));

                // Validate input data
                if (this._oCellEditor.validator) {
                    newData = this._oCellEditor.value = this._oCellEditor.validator.call(this, newData, oldData, this._oCellEditor);
                    if (newData === null) {
                        this.resetCellEditor();
                        this.fireEvent("editorRevertEvent",
                        {editor:this._oCellEditor, oldData:oldData, newData:newData});
                        YAHOO.log("Could not save Cell Editor input due to invalid data " +
                                  lang.dump(newData), "warn", this.toString());
                        return;
                    }
                }

                var editColumn = this._oCellEditor.column.key;
                var updateMethod;
                if(this.updateMethod){
                    updateMethod = this.updateMethod;
                }else{
                    updateMethod = "Update";
                }
                YAHOO.util.Connect.asyncRequest(
                        'POST',
                        '/rpc?action='+updateMethod+'&editColumn='+editColumn+'&newData=' + encodeURIComponent(newData) +
                        '&oldData=' + encodeURIComponent(oldData) + myBuildUrl(this, this._oCellEditor.record),
                {
                    success: function (o) {
                        // Update the Record
                        this._oRecordSet.updateRecordValue(this._oCellEditor.record, this._oCellEditor.column.key, this._oCellEditor.value);
                        // Update the UI
                        this.formatCell(this._oCellEditor.cell.firstChild);

                        // Bug fix 1764044
                        this._oChainRender.add({
                            method: function() {
                                this._syncColWidths();
                            },
                            scope: this
                        });
                        this._oChainRender.run();
                        // Clear out the Cell Editor
                        this.resetCellEditor();

                        this.fireEvent("editorSaveEvent",
                        {editor:this._oCellEditor, oldData:oldData, newData:newData});
                        YAHOO.log("Cell Editor input saved", "info", this.toString());
                    },
                    failure: function(o) {
                        onFailure(o.statusText);
                    },
                    scope: this
                }
                        );
            }
            else {
                YAHOO.log("Cell Editor not active to save input", "warn", this.toString());
            }
        };
        ;
    };
    ;
});
