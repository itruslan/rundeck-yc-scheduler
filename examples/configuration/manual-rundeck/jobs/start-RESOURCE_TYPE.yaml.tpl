# Template: Start job for a specific resource type.
#
# Generate from this template:
#   RESOURCE_TYPE=compute-instance
#   sed "s/RESOURCE_TYPE/$RESOURCE_TYPE/g" start-RESOURCE_TYPE.yaml.tpl > "start-${RESOURCE_TYPE}.yaml"

- defaultTab: nodes
  executionEnabled: true
  group: RESOURCE_TYPE
  loglevel: INFO
  name: Start
  nodeFilterEditable: true
  nodefilters:
    dispatch:
      excludePrecedence: true
      keepgoing: true
      rankAttribute: stop_order
      rankOrder: ascending
      successOnEmptyNodeFilter: false
      threadcount: "10"
    filter: "resource_type: RESOURCE_TYPE"
    # Exclude nodes by label (optional):
    # filterExclude: "labels:no_autoshutdown: true"
  nodesSelectedByDefault: true
  scheduleEnabled: false
  # Uncomment to enable scheduled execution:
  # scheduleEnabled: true
  # schedule:
  #   month: "*"
  #   time:
  #     hour: "07"
  #     minute: "00"
  #     seconds: "0"
  #   weekday:
  #     day: MON,TUE,WED,THU,FRI
  #   year: "*"
  # timeZone: Europe/Moscow
  sequence:
    commands:
      - nodeStep: true
        type: yc-start
        configuration:
          yc_sa_key: keys/project/${job.project}/yc-sa-key
    keepgoing: false
    strategy: node-first
