//YAHOO.util.Event.onContentReady('albumdiv', function() {
    var renderAlbumTable = function() {
        var myColumnDefs = [
            {key:"album_username",label:"Username",sortable:true,editor:"textbox"},
            {key:"album_type",label:"Access(picasaweb)",sortable:true,editor:"dropdown",editorOptions:{dropdownOptions:["public","private"]}},
            {key:"order",label:"Order",formatter:YAHOO.widget.DataTable.formatNumber,sortable:true,editor:"textbox",editorOptions:{validator:YAHOO.widget.DataTable.validateNumber}},
            {key:"valid",label:"Valid",sortable:true,editor:"radio",editorOptions:{radioOptions:[true,false],disableBtns:true}},
            {key:"id",label:"Id",sortable:true,isPrimaryKey:true},
            {key:"delete",label:"Del",action:'delete',formatter:function(elCell) {
                elCell.innerHTML = '<img src="/img/delete.gif" title="delete row" />';
                elCell.style.cursor = 'pointer';}},
            {key:"insert",label:"Add",action:'insert',formatter:function(elCell) {
                elCell.innerHTML = '<img src="/img/insert.png" title="insert new row" />';
                elCell.style.cursor = 'pointer';}}
        ];

        this.myDataSource = new YAHOO.util.DataSource(YAHOO.util.Dom.get("albumtable"));
        this.myDataSource.responseType = YAHOO.util.DataSource.TYPE_HTMLTABLE;
        this.myDataSource.responseSchema = {
            fields: [{key:"album_username"}, {key:"album_type"}, {key:"order"}, {key:"valid"},  {key:"id"}, {key:"delete"}, {key:"insert"}
            ]
        };
        this.myDataTable = new YAHOO.widget.DataTable("albumdiv", myColumnDefs, this.myDataSource,
           { sortedBy:{key:"album_username",dir:"asc"}});

        this.myDataTable.updateMethod = "UpdateAlbum";

        // Set up editing flow
        this.highlightEditableCell = function(oArgs) {
            var elCell = oArgs.target;
            if (YAHOO.util.Dom.hasClass(elCell, "yui-dt-editable")) {
                this.highlightCell(elCell);
            }
        };
        this.myDataTable.subscribe("cellMouseoverEvent", this.highlightEditableCell);
        this.myDataTable.subscribe("cellMouseoutEvent", this.myDataTable.onEventUnhighlightCell);
        //this.myDataTable.subscribe("cellClickEvent", this.myDataTable.onEventShowCellEditor);

        // Hook into custom event to customize save-flow of "radio" editor
        this.myDataTable.subscribe("editorUpdateEvent", function(oArgs) {
            if (oArgs.editor.column.key === "valid") {
                this.saveCellEditor();
            }
        });
        this.myDataTable.subscribe("editorBlurEvent", function(oArgs) {
            this.cancelCellEditor();
        });

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

        this.myDataTable.subscribe('cellClickEvent', function(ev) {
            var target = YAHOO.util.Event.getTarget(ev);
            var column = this.getColumn(target);
            if (column.action == 'insert') {
               if (confirm('Are you sure to add a new album?')) {
                   YAHOO.util.Connect.asyncRequest('POST', '/rpc?action=AddAlbum',
                   {
                       success: function (o) {
                               var record = YAHOO.lang.JSON.parse(o.responseText);
                               this.addRow(record ,this.getRecordIndex(target));
                        },
                       failure: function (o) {
                           alert(o.statusText);
                       },
                       scope:this
                   }
                           );
               }
            } else {
                this.onEventShowCellEditor(ev);
            }
        });

        this.myDataTable.subscribe('theadLabelDblclickEvent', function(ev) {
            var target = YAHOO.util.Event.getTarget(ev);
            //var column = this.getTheadEl(target);
            //if (column.label == 'insert') {
               if (confirm('Are you sure to add a new album?')) {
                   YAHOO.util.Connect.asyncRequest('POST', '/rpc?action=AddAlbum',
                   {
                       success: function (o) {
                               var record = YAHOO.lang.JSON.parse(o.responseText);
                               this.addRow(record ,this.getRecordIndex(target));
                        },
                       failure: function (o) {
                           alert(o.statusText);
                       },
                       scope:this
                   }
                           );
               }
            //} else {
            //    this.onEventShowCellEditor(ev);
           //}
        });

        this.myDataTable.subscribe('cellClickEvent', function(ev) {
            var target = YAHOO.util.Event.getTarget(ev);
            var column = this.getColumn(target);
            if (column.action == 'delete') {
                if (confirm('Are you sure to delete the album?')) {
                    var record = this.getRecord(target);
                    YAHOO.util.Connect.asyncRequest('POST','/rpc?action=DeleteAlbum' + myBuildUrl(this,record),
                    {
                        success: function (o) {
                            if (o.responseText == 'true') {
                                this.deleteRow(target);
                            } else {
                                alert(o.responseText);
                            }
                        },
                        failure: function (o) {
                            alert(o.statusText);
                        },
                        scope:this
                    }
                            );
                }
            } else {
                this.onEventShowCellEditor(ev);
            }
        });

        ;
    };
//});
